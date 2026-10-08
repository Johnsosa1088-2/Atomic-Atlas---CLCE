"""Independent NumPy checks on the JS spectral and phase numerical kernels."""
import json, subprocess, unittest
from pathlib import Path
import numpy as np

class ReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = """const X=require('./engines'),P=require('./phases');const atoms=['C','O','N','S'];
const A=[[0,1,1,0],[1,0,1,0],[1,1,0,1],[0,0,1,0]];
console.log(JSON.stringify({phaseLabs:['node','pairwise'].map(mode=>P.build(8,mode,42)),maskedPhase:P.build(4,'pairwise',42,A),atoms,A,spectral:new X.GlobalTopologyCLCEEngine().analyze_spectral_invariance(atoms,A),phase:new X.QuantumCoherenceCLCEEngine().compute_quantum_phase_coherence(atoms,A)}));"""
        run=subprocess.run(['node','-e',script],cwd=Path(__file__).parent,capture_output=True,text=True,check=True)
        cls.data=json.loads(run.stdout)
    def test_laplacian_eigenvalues(self):
        r=self.data['spectral'];W=np.array(r['weights']);L=np.diag(W.sum(axis=1))-W
        np.testing.assert_allclose(np.linalg.eigvalsh(L),r['eigenvalues'],atol=1e-10)
    def test_weights_from_distances(self):
        r=self.data['spectral'];coords=np.array(r['coordinates']);dist=np.linalg.norm(coords[:,None,:]-coords[None,:,:],axis=2)
        radii=np.array([.77,.73,.75,1.02]);ideal=radii[:,None]+radii[None,:]
        weights=np.array(self.data['A'])*np.exp(-3*np.abs(dist-ideal)/ideal)
        np.testing.assert_allclose(weights,r['weights'],atol=1e-12)
    def test_complex_phase_dominant_eigenvalue(self):
        r=self.data['phase'];coords=np.array(r['coordinates']);dist=np.linalg.norm(coords[:,None,:]-coords[None,:,:],axis=2)
        H=np.array(self.data['A'])*np.exp(1j*2*np.pi*dist/1.5)
        values,vectors=np.linalg.eigh(H,UPLO='L')
        self.assertAlmostEqual(values[-1],r['largest_eigenvalue'],places=9)
    def test_density_magnitude_and_score(self):
        r=self.data['phase'];self.assertFalse(r['degenerate'])
        coords=np.array(r['coordinates']);dist=np.linalg.norm(coords[:,None,:]-coords[None,:,:],axis=2)
        H=np.array(self.data['A'])*np.exp(1j*2*np.pi*dist/1.5)
        _,vectors=np.linalg.eigh(H,UPLO='L');v=vectors[:,-1];rho=np.abs(np.outer(v,np.conj(v)))
        np.testing.assert_allclose(rho,r['density_matrix_magnitude'],atol=1e-9)
        self.assertAlmostEqual((rho.sum()-np.trace(rho))/3,r['phase_coherence'],places=9)

    def test_phase_lab_spectra(self):
        for r in self.data['phaseLabs']:
            matrix=np.array([[complex(v['re'],v['im']) for v in row] for row in r['matrix']])
            np.testing.assert_allclose(matrix,matrix.conj().T,atol=1e-12)
            np.testing.assert_allclose(np.linalg.eigvalsh(matrix),r['diagnostics']['eigenvalues'],atol=1e-9)
    def test_masked_phase_lab_spectrum(self):
        r=self.data['maskedPhase']
        matrix=np.array([[complex(v['re'],v['im']) for v in row] for row in r['matrix']])
        np.testing.assert_allclose(np.linalg.eigvalsh(matrix),r['diagnostics']['eigenvalues'],atol=1e-9)
        self.assertEqual(np.trace(matrix),0)

if __name__=='__main__':unittest.main()

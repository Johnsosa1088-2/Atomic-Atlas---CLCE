from atlas_store import Store

if __name__ == '__main__':
    store=Store('example.sqlite')
    try:
        for rid,entity,state in [('lamp-001','lamp',{'power':{'value':5,'unit':'W'},'enabled':True}),
                                 ('decision-001','retrieval experiment',{'decision':'Compare ordinary retrieval with atlas-organized retrieval','status':'planned','benefit':'not established'}),
                                 ('lamp-002','lamp',{'power':{'value':3,'unit':'W'},'enabled':False})]:
            store.append(rid,entity,state,{'locator':'synthetic:bridge/'+rid,'evidence':'synthetic'},store.verify())
        print('Saved durable synthetic example.sqlite. Re-running identical seed is safe.')
    finally:store.close()

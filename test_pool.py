import concurrent.futures

def load_idf(path):
    import warnings
    warnings.filterwarnings('ignore')
    try:
        from accim.utils import get_building
        b = get_building(path)
        return 'success_get_building'
    except Exception as e:
        import traceback
        return traceback.format_exc()

if __name__ == '__main__':
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as ex:
        res = list(ex.map(load_idf, ['SF_Detached_A_max_South.idf']))
        print(res)

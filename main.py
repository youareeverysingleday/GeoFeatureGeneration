
import GeoFeatureGeneration as gfg

if __name__ == '__main__':
    gfg.GetParameters('./Parameters.json')
    # print(gfg.gGeoParameters)
    gfg.GenerateGeoFeature()

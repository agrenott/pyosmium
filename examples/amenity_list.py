"""
Extract objects with an amenity tag from an osm file and list them
with their name and position.

Points and areas will be processed, unclosed ways will be skipped.

Points and areas will be processed, unclosed ways will be skipped.

This example shows how geometries from npyosmium objects can be imported
into shapely using the WKBFactory.
"""
import npyosmium as o
import sys
import shapely.wkb as wkblib

wkbfab = o.geom.WKBFactory()

class AmenityListHandler(o.SimpleHandler):

    def print_amenity(self, tags, lon, lat):
        name = tags.get('name', '')
        print("%f %f %-15s %s" % (lon, lat, tags['amenity'], name))

    def node(self, n):
        self.print_amenity(n.tags, n.location.lon, n.location.lat)

    def area(self, a):
        wkb = wkbfab.create_multipolygon(a)
        poly = wkblib.loads(wkb, hex=True)
        centroid = poly.representative_point()
        self.print_amenity(a.tags, centroid.x, centroid.y)


def main(osmfile):

    handler = AmenityListHandler()

    handler.apply_file(osmfile, filters=[o.filter.KeyFilter('amenity')])

    return 0

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python %s <osmfile>" % sys.argv[0])
        sys.exit(-1)

    exit(main(sys.argv[1]))


def gpoly_encode(points):
    """
    Expose the encode method from gpolyencode library

    points (list): list of latlon 2-tuples.
    
    """
    try:
        import gpolyencode
        encoder = gpolyencode.GPolyEncoder()
    except Exception as err:
        return dict(error='%s: %s' % (type(err), err, ))
    else:
        return encoder.encode(points)

def decode_line(encoded):
    """
    Coutesy of: http://seewah.blogspot.it/2009/11/gpolyline-decoding-in-python.html
    Decodes a polyline that was encoded using the Google Maps method.

    See http://code.google.com/apis/maps/documentation/polylinealgorithm.html

    This is a straightforward Python port of Mark McClure's JavaScript polyline decoder
    (http://facstaff.unca.edu/mcmcclur/GoogleMaps/EncodePolyline/decode.js)
    and Peter Chng's PHP polyline decode
    (http://unitstep.net/blog/2008/08/02/decoding-google-maps-encoded-polylines-using-php/)

    encoded (str): encoded latlon sequence.
    
    """

    encoded_len = len(encoded)
    index = 0
    array = []
    lat = 0
    lng = 0

    while index < encoded_len:

        b = 0
        shift = 0
        result = 0

        while True:
            b = ord(encoded[index]) - 63
            index = index + 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break

        dlat = ~(result >> 1) if result & 1 else result >> 1
        lat += dlat

        shift = 0
        result = 0

        while True:
            b = ord(encoded[index]) - 63
            index = index + 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break

        dlng = ~(result >> 1) if result & 1 else result >> 1
        lng += dlng

        array.append((lat * 1e-5, lng * 1e-5))

    return array

if __name__ == "__main__":
    """ Test """
    encoded_points = "grkyHhpc@B[[_IYiLiEgj@a@q@yEoAGi@bEyH_@aHj@m@^qAB{@IkHi@cHcAkPSiMJqEj@s@CkFp@sDfB}Ex@iBj@S_AyIkCcUWgAaA_JUyAFk@{D_]~KiLwAeCsHqJmBlAmFuXe@{DcByIZIYiBxBwAc@eCcAl@y@aEdCcBVJpHsEyAeE"
    latlngs = decode_line(encoded_points)
    latlngs2 = decode_line(gpoly_encode(latlngs).get('points'))
    for latlng in zip(latlngs, latlngs):
        assert latlng[0][0]==latlng[1][0] and latlng[0][1]==latlng[1][1]
    print "Test passed!"

    #print gpoly_encode(latlngs)
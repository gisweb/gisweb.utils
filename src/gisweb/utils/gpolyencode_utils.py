import gpolyencode

def gpoly_encode(points):
	try:
		encoder = gpolyencode.GPolyEncoder()
		return encoder.encode(points)
	except:
		return dict(error:'Errore')
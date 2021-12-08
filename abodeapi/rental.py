# Add price from
# Add url

class Rental(object):
    title = ""
    description_about = ""
    description_surrounds = ""
    facilities = []
    images = []
    phone = ""
    url = ""
    email = ""
    rates = ""
    lat = ""
    long = ""
    address = ""
    source = ""
    rentaltype_id = -1
    feature_ids = []

    def __init__(self):
        self.title = ""
        self.description_about = ""
        self.description_surrounds = ""
        self.facilities = []
        self.images = []
        self.phone = ""
        self.url = ""
        self.email = ""
        self.rates = ""
        self.lat = ""
        self.long = ""
        self.address = ""
        self.source = ""
        self.rentaltype_id = -1
        self.feature_ids = []

    def __repr__(self):
        return 'Title: %s\n\n' \
               'Description about: %s\n\n' \
               'Facilities: %s\n\n' \
               'Images: %s\n\n' \
               'Coordinates: %s, %s\n\n' \
               'Rates: %s\n\n' \
               'Address: %s\n\n' \
               'Phone: %s\n\n' \
               'Email: %s\n\n' \
               'URL: %s\n\n' \
               'Source: %s\n\n' \
               'RentalType ID: %s\n\n' \
               'Feature ID: %s\n\n' \
               % (self.title, self.description_about, str(self.facilities),
                  str(self.images), self.lat, self.long, self.rates, self.address,
                  self.phone, self.email, self.url, self.source, self.rentaltype_id,
                  str(self.feature_ids))



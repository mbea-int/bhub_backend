fake_businesses = [
    # Restaurants (2)
    {
        "user_email": "ardiana.hoxha@gmail.com",
        "business_name": "Restoranti Tradicional Shqiptar",
        "slug": "restoranti-tradicional-shqiptar",
        "description": "Restoranti ynë ofron ushqime tradicionale shqiptare të përgatitura me receta të trashëguara brez pas brezi. Të gjitha produktet janë 100% halal dhe të certifikuara.",
        "category": "restaurant",
        "logo": "https://via.placeholder.com/200x200/F59E0B/FFFFFF?text=RTS",
        "phone": "+355694444555",
        "email": "info@restoranti-tradicional.al",
        "address": "Rruga Myslym Shyri, Nr. 45",
        "city": "Tiranë",
        "country": "Albania",
        "latitude": 41.3275,
        "longitude": 19.8187,
        "business_hours": {
            "monday": {"open": "08:00", "close": "22:00", "is_closed": False},
            "tuesday": {"open": "08:00", "close": "22:00", "is_closed": False},
            "wednesday": {"open": "08:00", "close": "22:00", "is_closed": False},
            "thursday": {"open": "08:00", "close": "22:00", "is_closed": False},
            "friday": {"open": "11:00", "close": "23:00", "is_closed": False},
            "saturday": {"open": "09:00", "close": "23:00", "is_closed": False},
            "sunday": {"open": "09:00", "close": "22:00", "is_closed": False}
        },
        "is_verified": True,
        "is_premium": True,
        "is_halal_certified": True,
        "social_instagram": "@restoranti_tradicional",
        "social_facebook": "restoranti.tradicional.al",
        "average_rating": 4.8,
        "total_reviews": 234,
        "total_followers": 567,
        "is_primary": True
    },
    {
        "user_email": "fationa.berisha@gmail.com",
        "business_name": "Kuzhina e Nënës",
        "slug": "kuzhina-e-nenes",
        "description": "Ushqim shtëpiak i përgatitur me dashuri. Specialitete të ndryshme çdo ditë, të gjitha halal.",
        "category": "restaurant",
        "phone": "+355695555666",
        "email": "info@kuzhina-nenes.al",
        "address": "Rruga Barrikadave, Nr. 123",
        "city": "Tiranë",
        "average_rating": 4.5,
        "total_reviews": 156,
        "is_primary": True
    },

    # Markets (2)
    {
        "user_email": "besmira.krasniqi@gmail.com",
        "business_name": "Halal Market Tirana",
        "slug": "halal-market-tirana",
        "description": "Supermarket me produkte ekskluzivisht halal. Importojmë produkte nga vende të ndryshme muslimane.",
        "category": "market",
        "phone": "+355696666777",
        "email": "info@halal-market.al",
        "address": "Rruga Ibrahim Rugova, Nr. 67",
        "city": "Tiranë",
        "is_verified": True,
        "is_halal_certified": True,
        "average_rating": 4.6,
        "total_reviews": 189,
        "total_followers": 234,
        "is_primary": True
    },

    # Clothing Stores (2)
    {
        "user_email": "ermela.shehu@gmail.com",
        "business_name": "Modest Fashion Albania",
        "slug": "modest-fashion-albania",
        "description": "Veshje moderne dhe modeste për gratë muslimane. Koleksione të reja çdo sezon.",
        "category": "clothing-store",
        "phone": "+355698888999",
        "email": "info@modest-fashion.al",
        "address": "Qendra Tregtare Toptani, Kati 2",
        "city": "Tiranë",
        "is_premium": True,
        "average_rating": 4.7,
        "total_reviews": 98,
        "is_primary": True
    },
    {
        "user_email": "ardiana.hoxha@gmail.com",
        "business_name": "Butiku Eleganca",
        "slug": "butiku-eleganca",
        "description": "Veshje tradicionale dhe moderne për të gjithë familjen.",
        "category": "clothing-store",
        "address": "Rruga e Kavajës, Nr. 89",
        "city": "Tiranë",
        "average_rating": 4.3,
        "total_reviews": 67,
        "is_primary": False
    },

    # Barbershops (1)
    {
        "user_email": "besmira.krasniqi@gmail.com",
        "business_name": "The Gentleman Barber",
        "slug": "the-gentleman-barber",
        "description": "Berber profesional për burra. Prerje moderne dhe tradicionale.",
        "category": "barbershop",
        "address": "Rruga Sami Frashëri, Nr. 34",
        "city": "Tiranë",
        "average_rating": 4.9,
        "total_reviews": 145,
        "is_primary": False
    },

    # Mosques (2)
    {
        "user_email": "fationa.berisha@gmail.com",
        "business_name": "Xhamia e Re",
        "slug": "xhamia-e-re",
        "description": "Xhami moderne me ambiente të ndara për burra dhe gra. Programe edukative për të rinjtë.",
        "category": "mosque",
        "address": "Rruga e Dibrës, Nr. 200",
        "city": "Tiranë",
        "is_verified": True,
        "average_rating": 4.9,
        "total_reviews": 45,
        "is_primary": False
    },

    # Islamic Schools (1)
    {
        "user_email": "ermela.shehu@gmail.com",
        "business_name": "Shkolla Kurani",
        "slug": "shkolla-kurani",
        "description": "Mësime Kurani dhe gjuhës arabe për të gjitha moshat.",
        "category": "islamic-school",
        "address": "Rruga Muhamet Gjollesha, Nr. 56",
        "city": "Tiranë",
        "average_rating": 4.8,
        "total_reviews": 34,
        "is_primary": False
    },

    # Bakeries (2)
    {
        "user_email": "ardiana.hoxha@gmail.com",
        "business_name": "Furra Halal",
        "slug": "furra-halal",
        "description": "Produkte furre të freskëta çdo ditë. Të gjitha produktet janë halal.",
        "category": "bakery",
        "address": "Rruga Vaso Pasha, Nr. 12",
        "city": "Tiranë",
        "is_halal_certified": True,
        "average_rating": 4.6,
        "total_reviews": 123,
        "is_primary": False
    },

    # Healthcare (1)
    {
        "user_email": "fationa.berisha@gmail.com",
        "business_name": "Klinika Medicus",
        "slug": "klinika-medicus",
        "description": "Klinikë me staf musliman dhe ambiente të ndara për pacientë.",
        "category": "healthcare",
        "address": "Rruga Qemal Stafa, Nr. 78",
        "city": "Tiranë",
        "is_verified": True,
        "average_rating": 4.7,
        "total_reviews": 89,
        "is_primary": False
    }
]
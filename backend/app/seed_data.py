from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from app.db.session import Base, SessionLocal, engine
from app.models import Product, Shop, ShopStaff, Subscription, User
from app.models.enums import SubscriptionPlan, SubscriptionStatus, UserRole

SEED_SHOPS = (
    {
        "name": "KahveCell Kızılay",
        "address": "15 Temmuz Kızılay Millî İrade Meydanı çevresi, Çankaya, Ankara",
        "latitude": 39.9209927,
        "longitude": 32.8540176,
        "products": (
            ("Espresso", "Tek shot espresso", "90.00"),
            ("Cappuccino", "Espresso ve süt köpüğü", "145.00"),
            ("Türk kahvesi", "Geleneksel Türk kahvesi", "115.00"),
            ("Latte", "Espresso ve buharda ısıtılmış süt", "155.00"),
        ),
    },
    {
        "name": "KahveCell Tunalı",
        "address": "Tunalı Hilmi Caddesi, Barbaros Mahallesi, Çankaya, Ankara",
        "latitude": 39.9063106,
        "longitude": 32.8609281,
        "products": (
            ("Espresso", "Tek shot espresso", "100.00"),
            ("Cappuccino", "Espresso ve süt köpüğü", "160.00"),
            ("Türk kahvesi", "Geleneksel Türk kahvesi", "125.00"),
            ("Latte", "Espresso ve buharda ısıtılmış süt", "170.00"),
        ),
    },
    {
        "name": "KahveCell Bahçelievler",
        "address": "Bahçelievler Mahallesi, Çankaya, Ankara",
        "latitude": 39.927807,
        "longitude": 32.8264893,
        "products": (
            ("Espresso", "Tek shot espresso", "85.00"),
            ("Cappuccino", "Espresso ve süt köpüğü", "135.00"),
            ("Türk kahvesi", "Geleneksel Türk kahvesi", "105.00"),
            ("Latte", "Espresso ve buharda ısıtılmış süt", "145.00"),
        ),
    },
    {
        "name": "KahveCell Çayyolu",
        "address": "Çayyolu, Çankaya, Ankara",
        "latitude": 39.881335,
        "longitude": 32.6837649,
        "products": (
            ("Espresso", "Tek shot espresso", "95.00"),
            ("Cappuccino", "Espresso ve süt köpüğü", "150.00"),
            ("Türk kahvesi", "Geleneksel Türk kahvesi", "120.00"),
            ("Latte", "Espresso ve buharda ısıtılmış süt", "165.00"),
        ),
    },
    {
        "name": "KahveCell Oran",
        "address": "Panora AVM, Kudüs Caddesi, Or-An Mahallesi, Çankaya, Ankara",
        "latitude": 39.8481429,
        "longitude": 32.8330449,
        "products": (
            ("Espresso", "Tek shot espresso", "105.00"),
            ("Cappuccino", "Espresso ve süt köpüğü", "165.00"),
            ("Türk kahvesi", "Geleneksel Türk kahvesi", "130.00"),
            ("Latte", "Espresso ve buharda ısıtılmış süt", "175.00"),
        ),
    },
)

DEMO_PHONE_NUMBER = "+905550000001"
DEMO_SHOP_OWNER_PHONE_NUMBER = "+905550000002"


def seed_demo_data() -> None:
    with SessionLocal() as database:
        added_shops = 0
        added_products = 0

        for shop_data in SEED_SHOPS:
            shop = database.scalar(
                select(Shop).where(Shop.name == shop_data["name"])
            )
            if shop is None:
                shop = Shop(
                    name=shop_data["name"],
                    address=shop_data["address"],
                    latitude=shop_data["latitude"],
                    longitude=shop_data["longitude"],
                    opening_hours={"weekdays": "08:00-22:00", "weekends": "09:00-23:00"},
                )
                database.add(shop)
                database.flush()
                added_shops += 1

            for name, description, price in shop_data["products"]:
                existing_product = database.scalar(
                    select(Product).where(
                        Product.shop_id == shop.id,
                        Product.name == name,
                    )
                )
                if existing_product is None:
                    database.add(
                        Product(
                            shop_id=shop.id,
                            name=name,
                            description=description,
                            price=Decimal(price),
                        )
                    )
                    added_products += 1

        demo_user = database.scalar(
            select(User).where(User.phone_number == DEMO_PHONE_NUMBER)
        )
        added_starter = False
        if demo_user is None:
            demo_user = User(
                phone_number=DEMO_PHONE_NUMBER,
                full_name="KahveCell Demo Kullanıcısı",
                role=UserRole.CUSTOMER,
            )
            database.add(demo_user)
            database.flush()

        starter_subscription = database.scalar(
            select(Subscription).where(
                Subscription.user_id == demo_user.id,
                Subscription.plan_type == SubscriptionPlan.STARTER,
                Subscription.status == SubscriptionStatus.ACTIVE,
            )
        )
        if starter_subscription is None:
            started_at = datetime.now(timezone.utc)
            database.add(
                Subscription(
                    user_id=demo_user.id,
                    plan_type=SubscriptionPlan.STARTER,
                    remaining_credits=10,
                    status=SubscriptionStatus.ACTIVE,
                    started_at=started_at,
                    expires_at=started_at + timedelta(days=30),
                )
            )
            added_starter = True

        shop_owner = database.scalar(
            select(User).where(User.phone_number == DEMO_SHOP_OWNER_PHONE_NUMBER)
        )
        if shop_owner is None:
            shop_owner = User(
                phone_number=DEMO_SHOP_OWNER_PHONE_NUMBER,
                full_name="KahveCell Demo Dükkân Sahibi",
                role=UserRole.SHOP_OWNER,
            )
            database.add(shop_owner)
            database.flush()

        for shop in database.scalars(select(Shop)).all():
            assignment = database.scalar(
                select(ShopStaff.id).where(
                    ShopStaff.user_id == shop_owner.id,
                    ShopStaff.shop_id == shop.id,
                )
            )
            if assignment is None:
                database.add(ShopStaff(user_id=shop_owner.id, shop_id=shop.id))

        database.commit()

    print(
        "Ankara seed tamamlandı: "
        f"{added_shops} dükkân, {added_products} ürün, "
        f"Starter aboneliği {'oluşturuldu' if added_starter else 'zaten mevcut'}."
    )


def main() -> None:
    Base.metadata.create_all(bind=engine)
    seed_demo_data()


if __name__ == "__main__":
    main()
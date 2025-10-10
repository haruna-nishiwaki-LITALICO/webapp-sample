import os
import sys
from typing import Dict, Tuple, Any, Optional

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    abort,
)
from flask_sqlalchemy import SQLAlchemy
from markupsafe import Markup

app = Flask(__name__)
app.config["SECRET_KEY"] = "qa-practice-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///qa_practice.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db = SQLAlchemy(app)


CATEGORIES = ["書籍", "家電", "食品", "その他"]
STATUSES = ["準備中", "公開中", "非公開"]

USERS: Dict[str, Dict[str, str]] = {
    "admin": {"password": "admin_password", "role": "admin"},
    "user": {"password": "user_password", "role": "user"},
}


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(10), nullable=False, default="準備中")

    def allowed_status_transitions(self) -> Tuple[str, ...]:
        transitions = {
            "準備中": ("公開中", "非公開"),
            "公開中": ("非公開",),
            "非公開": ("公開中",),
        }
        return transitions.get(self.status, tuple())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def current_user_role() -> Optional[str]:
    return session.get("role")


def is_logged_in() -> bool:
    return "user_id" in session


def require_login():
    if not is_logged_in():
        flash("ログインが必要です。", "warning")
        return redirect(url_for("login"))
    return None


def require_role(role: str):
    if current_user_role() != role:
        flash("権限が不足しています。", "error")
        return redirect(url_for("list_products"))
    return None


def parse_int(value: str, field: str, errors: Dict[str, str], *, min_value: int, max_value: int) -> Optional[int]:
    if value == "" or value is None:
        errors[field] = "必須入力です。"
        return None
    try:
        number = int(value)
    except ValueError:
        errors[field] = "数値を入力してください。"
        return None
    if number < min_value or number > max_value:
        errors[field] = f"{min_value}以上{max_value}以下で入力してください。"
        return None
    return number


def validate_product_form(form: Dict[str, Any], *, product: Optional[Product] = None) -> Tuple[Dict[str, Any], Dict[str, str]]:
    errors: Dict[str, str] = {}
    cleaned: Dict[str, Any] = {}

    name = (form.get("name") or "").strip()
    if not name:
        errors["name"] = "商品名は必須です。"
    elif len(name) < 1 or len(name) > 50:
        errors["name"] = "商品名は1文字以上50文字以下で入力してください。"
    cleaned["name"] = name

    category = form.get("category")
    if category not in CATEGORIES:
        errors["category"] = "カテゴリを選択してください。"
    cleaned["category"] = category

    price = parse_int(form.get("price", ""), "price", errors, min_value=0, max_value=1_000_000)
    if price is not None:
        cleaned["price"] = price

    stock = parse_int(form.get("stock", ""), "stock", errors, min_value=0, max_value=999)
    if stock is not None:
        cleaned["stock"] = stock

    description = form.get("description") or ""
    cleaned["description"] = description

    requested_status = form.get("status") or "準備中"

    if product is None:
        cleaned["status"] = "準備中"
    else:
        if requested_status not in STATUSES:
            errors["status"] = "ステータスを選択してください。"
        elif requested_status != product.status and requested_status not in product.allowed_status_transitions():
            errors["status"] = "このステータスには変更できません。"
        else:
            cleaned["status"] = requested_status

    return cleaned, errors


def stock_indication(product: Product) -> Tuple[str, str]:
    if product.stock == 0:
        return "在庫切れ", "stock-empty"
    if 1 <= product.stock <= 10:
        return "残りわずか", "stock-low"
    return "在庫あり", "stock-ok"


def initialize_database(with_samples: bool = True) -> None:
    db.create_all()
    if not with_samples:
        return

    if Product.query.count() > 0:
        return

    samples = [
        Product(
            name="自動テスト入門",
            category="書籍",
            price=3200,
            stock=5,
            description="自動テストの基礎を学べる書籍です。",
            status="公開中",
        ),
        Product(
            name="デバッグマスター",
            category="書籍",
            price=2800,
            stock=0,
            description="開発者とQAのためのデバッグ虎の巻。",
            status="非公開",
        ),
        Product(
            name="テスト自動化トレーニングキット",
            category="家電",
            price=58000,
            stock=12,
            description="Selenium対応のラボ環境デバイス。",
            status="準備中",
        ),
        Product(
            name="集中力を保つ栄養バー",
            category="食品",
            price=380,
            stock=9,
            description="テスト実行前に最適なスナック。",
            status="公開中",
        ),
    ]
    db.session.add_all(samples)
    db.session.commit()


with app.app_context():
    initialize_database()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    if is_logged_in():
        return redirect(url_for("list_products"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user_id = (request.form.get("user_id") or "").strip()
        password = request.form.get("password") or ""

        user = USERS.get(user_id)
        if not user or user["password"] != password:
            flash("IDまたはパスワードが正しくありません。", "error")
        else:
            session["user_id"] = user_id
            session["role"] = user["role"]
            flash("ログインしました。", "success")
            return redirect(url_for("list_products"))

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("ログアウトしました。", "info")
    return redirect(url_for("login"))


@app.route("/products")
def list_products():
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    keyword = (request.args.get("keyword") or "").strip()
    category = request.args.get("category") or ""
    min_price = request.args.get("min_price") or ""
    max_price = request.args.get("max_price") or ""

    if keyword and "バグ票" in keyword:
        # Intentional defect for testing practice
        raise RuntimeError("Intentional bug triggered by keyword バグ票")

    query = Product.query

    if keyword:
        like_pattern = f"%{keyword}%"
        query = query.filter(
            db.or_(
                Product.name.like(like_pattern),
                Product.description.like(like_pattern),
            )
        )

    if category and category in CATEGORIES:
        query = query.filter(Product.category == category)

    try:
        if min_price:
            query = query.filter(Product.price >= int(min_price))
        if max_price:
            query = query.filter(Product.price <= int(max_price))
    except ValueError:
        flash("価格は数値で入力してください。", "warning")

    products = query.order_by(Product.id.asc()).all()

    product_rows = []
    for product in products:
        status_label, status_class = stock_indication(product)
        product_rows.append(
            {
                "product": product,
                "stock_label": status_label,
                "row_class": status_class,
                "description_markup": Markup(product.description or ""),
            }
        )

    return render_template(
        "products.html",
        products=product_rows,
        categories=CATEGORIES,
        keyword=keyword,
        selected_category=category,
        min_price=min_price,
        max_price=max_price,
        role=current_user_role(),
    )


@app.route("/products/new", methods=["GET", "POST"])
def new_product():
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    role_redirect = require_role("admin")
    if role_redirect:
        return role_redirect

    if request.method == "POST":
        cleaned, errors = validate_product_form(request.form)
        if errors:
            for field, message in errors.items():
                flash(f"{field}: {message}", "error")
            return render_template(
                "product_form.html",
                form=request.form,
                errors=errors,
                categories=CATEGORIES,
                status_options=["準備中"],
                form_action=url_for("new_product"),
                submit_label="登録",
                is_new=True,
            )

        product = Product(**cleaned)
        db.session.add(product)
        db.session.commit()
        flash("商品を登録しました。", "success")
        return redirect(url_for("list_products"))

    return render_template(
        "product_form.html",
        form={},
        errors={},
        categories=CATEGORIES,
        status_options=["準備中"],
        form_action=url_for("new_product"),
        submit_label="登録",
        is_new=True,
    )


@app.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
def edit_product(product_id: int):
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    product = Product.query.get_or_404(product_id)

    if request.method == "POST":
        cleaned, errors = validate_product_form(request.form, product=product)
        if errors:
            for field, message in errors.items():
                flash(f"{field}: {message}", "error")
            return render_template(
                "product_form.html",
                form=request.form,
                errors=errors,
                categories=CATEGORIES,
                status_options=STATUSES,
                form_action=url_for("edit_product", product_id=product_id),
                submit_label="更新",
                is_new=False,
                product=product,
            )

        product.name = cleaned["name"]
        product.category = cleaned["category"]
        product.price = cleaned["price"]
        product.stock = cleaned["stock"]
        product.description = cleaned["description"]
        if "status" in cleaned:
            product.status = cleaned["status"]

        db.session.commit()
        flash("商品情報を更新しました。", "success")
        return redirect(url_for("list_products"))

    form_data = {
        "name": product.name,
        "category": product.category,
        "price": product.price,
        "stock": product.stock,
        "description": product.description,
        "status": product.status,
    }

    return render_template(
        "product_form.html",
        form=form_data,
        errors={},
        categories=CATEGORIES,
        status_options=STATUSES,
        form_action=url_for("edit_product", product_id=product_id),
        submit_label="更新",
        is_new=False,
        product=product,
    )


@app.route("/products/<int:product_id>/delete", methods=["POST"])
def delete_product(product_id: int):
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    role_redirect = require_role("admin")
    if role_redirect:
        return role_redirect

    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash("商品を削除しました。", "info")
    return redirect(url_for("list_products"))


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def handle_cli_commands() -> bool:
    if len(sys.argv) <= 1:
        return False

    command = sys.argv[1]
    if command == "--init-db":
        with app.app_context():
            initialize_database(with_samples=True)
        print("Database initialized with sample data.")
        return True
    if command == "--reset-db":
        db_path = app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")
        if os.path.exists(db_path):
            os.remove(db_path)
        with app.app_context():
            initialize_database(with_samples=True)
        print("Database reset with sample data.")
        return True
    return False


if __name__ == "__main__":
    if not handle_cli_commands():
        app.run(debug=True)

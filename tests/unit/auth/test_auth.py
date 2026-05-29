import pytest
from flask import url_for

from app import db, login_required
from app.models import Role, User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def login(client, email, password):
    """Log a user in via the real /login endpoint."""
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )


def register_probe_route(app, rule, endpoint, role):
    """Attach a trivial role-gated route to the app for decorator testing.

    The view just returns a 200 with a marker string when access is allowed,
    so the only thing under test is the decorator's allow/deny decision.
    """

    @login_required(role=role)
    def _probe():
        return "ALLOWED"

    _probe.__name__ = endpoint
    app.add_url_rule(rule, endpoint, _probe)


# ===========================================================================
# login_required decorator
# ===========================================================================
class TestLoginRequiredDecorator:
    def test_unauthenticated_user_is_rejected(self, app, client):
        register_probe_route(app, "/_probe_any", "_probe_any", ["any"])
        resp = client.get("/_probe_any")
        # flask-login's unauthorized handler redirects to the login view
        assert resp.status_code in (302, 401)
        assert b"ALLOWED" not in resp.data

    def test_authenticated_user_passes_any_role(self, app, client):
        register_probe_route(app, "/_probe_any2", "_probe_any2", ["any"])
        force_login(client, app, "test@example.com")
        resp = client.get("/_probe_any2")
        assert resp.status_code == 200
        assert resp.data == b"ALLOWED"

    def test_user_with_required_role_is_allowed(self, app, client):
        register_probe_route(app, "/_probe_user", "_probe_user", ["user"])
        force_login(client, app, "test@example.com")
        resp = client.get("/_probe_user")
        assert resp.status_code == 200
        assert resp.data == b"ALLOWED"

    def test_user_missing_required_role_is_denied(self, app, client):
        # test@example.com has only the "user" role, not "admin"
        register_probe_route(app, "/_probe_admin", "_probe_admin", ["admin"])
        force_login(client, app, "test@example.com")
        resp = client.get("/_probe_admin")
        assert resp.status_code in (302, 401)
        assert b"ALLOWED" not in resp.data

    def test_admin_with_all_roles_passes_multi_role_gate(self, app, client):
        register_probe_route(app, "/_probe_bc", "_probe_bc", ["coreB", "coreC"])
        force_login(client, app, "admin@example.com")
        resp = client.get("/_probe_bc")
        assert resp.status_code == 200
        assert resp.data == b"ALLOWED"

    def test_user_denied_when_missing_one_of_multiple_required_roles(self, app, client):
        # Requires both coreB AND coreC; plain user has neither.
        register_probe_route(app, "/_probe_bc2", "_probe_bc2", ["coreB", "coreC"])
        force_login(client, app, "test@example.com")
        resp = client.get("/_probe_bc2")
        assert resp.status_code in (302, 401)
        assert b"ALLOWED" not in resp.data

    def test_any_short_circuits_before_role_checks(self, app, client):
        """The 'any' keyword should allow access regardless of which other
        roles are listed after it, because the loop breaks on 'any'."""
        register_probe_route(
            app, "/_probe_anyfirst", "_probe_anyfirst", ["any", "admin"]
        )
        force_login(client, app, "test@example.com")  # not an admin
        resp = client.get("/_probe_anyfirst")
        assert resp.status_code == 200
        assert resp.data == b"ALLOWED"


# ===========================================================================
# /login
# ===========================================================================
class TestLogin:
    def test_get_renders_login_page(self, client):
        resp = client.get("/login")
        assert resp.status_code == 200

    def test_valid_login_redirects(self, client):
        # admin has coreB, so the handler redirects to orders.orders
        resp = login(client, "admin@example.com", "admin")
        assert resp.status_code == 302

    def test_wrong_password_redirects_back_to_login(self, client):
        resp = login(client, "admin@example.com", "wrong-password")
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_nonexistent_user_redirects_back_to_login(self, client):
        resp = login(client, "nobody@example.com", "whatever")
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_email_is_normalized_before_lookup(self, client):
        # Seeded email is lowercase; logging in with mixed case + whitespace
        # should still authenticate because the handler strips/lowercases.
        resp = login(client, "  ADMIN@EXAMPLE.COM  ", "admin")
        assert resp.status_code == 302
        assert "/login" not in resp.headers["Location"]


# ===========================================================================
# /signup  (admin-only: add users / view admin panel)
# ===========================================================================
class TestSignup:
    def test_signup_get_requires_auth(self, client):
        resp = client.get("/signup")
        assert resp.status_code in (302, 401)

    def test_signup_get_as_admin_renders(self, app, client):
        force_login(client, app, "admin@example.com")
        resp = client.get("/signup")
        assert resp.status_code == 200

    def test_signup_creates_new_user(self, app, client):
        force_login(client, app, "admin@example.com")
        resp = client.post(
            "/signup",
            data={
                "email": "newperson@example.com",
                "name": "New Person",
                "password": "secret123",
                "core": "B",
                "permision": "u",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302
        with app.app_context():
            created = User.query.filter_by(email="newperson@example.com").first()
            assert created is not None
            assert created.name == "New Person"
            # password must be stored hashed, never in plaintext
            assert created.password != "secret123"

    def test_signup_assigns_admin_and_user_roles(self, app, client):
        force_login(client, app, "admin@example.com")
        client.post(
            "/signup",
            data={
                "email": "newadmin@example.com",
                "name": "New Admin",
                "password": "secret123",
                "core": "C",
                "permision": "a",
            },
        )
        with app.app_context():
            created = User.query.filter_by(email="newadmin@example.com").first()
            roles = {r.role for r in created.urole}
            assert "admin" in roles
            assert "user" in roles
            assert "coreC" in roles

    def test_signup_core_bc_assigns_both_cores(self, app, client):
        force_login(client, app, "admin@example.com")
        client.post(
            "/signup",
            data={
                "email": "bcuser@example.com",
                "name": "BC User",
                "password": "secret123",
                "core": "BC",
                "permision": "u",
            },
        )
        with app.app_context():
            created = User.query.filter_by(email="bcuser@example.com").first()
            roles = {r.role for r in created.urole}
            assert "coreB" in roles
            assert "coreC" in roles

    def test_signup_empty_fields_redirects_without_creating(self, app, client):
        force_login(client, app, "admin@example.com")
        resp = client.post(
            "/signup",
            data={
                "email": "",
                "name": "",
                "password": "",
                "core": "B",
                "permision": "u",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302
        with app.app_context():
            assert User.query.filter_by(email="").first() is None

    def test_signup_duplicate_email_does_not_create_second(self, app, client):
        force_login(client, app, "admin@example.com")
        resp = client.post(
            "/signup",
            data={
                "email": "test@example.com",  # already seeded
                "name": "Dupe",
                "password": "secret123",
                "core": "B",
                "permision": "u",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302
        with app.app_context():
            assert User.query.filter_by(email="test@example.com").count() == 1

    def test_signup_email_is_normalized_on_create(self, app, client):
        force_login(client, app, "admin@example.com")
        client.post(
            "/signup",
            data={
                "email": "  MixedCase@Example.COM  ",
                "name": "Mixed",
                "password": "secret123",
                "core": "B",
                "permision": "u",
            },
        )
        with app.app_context():
            assert (
                User.query.filter_by(email="mixedcase@example.com").first() is not None
            )

    def test_non_admin_cannot_access_signup(self, app, client):
        force_login(client, app, "test@example.com")  # plain user
        resp = client.get("/signup")
        assert resp.status_code in (302, 401)


# ===========================================================================
# /deleteUser  (admin-only)
# ===========================================================================
class TestDeleteUser:
    def test_delete_existing_user(self, app, client):
        # seed a throwaway user to delete
        with app.app_context():
            user_role = Role.query.filter_by(role="user").first()
            victim = User(
                email="victim@example.com",
                name="Victim",
                password="x",
            )
            victim.urole.append(user_role)
            db.session.add(victim)
            db.session.commit()

        force_login(client, app, "admin@example.com")
        resp = client.get(
            "/deleteUser?email=victim@example.com", follow_redirects=False
        )
        assert resp.status_code == 302
        with app.app_context():
            assert User.query.filter_by(email="victim@example.com").first() is None

    def test_delete_nonexistent_user_still_redirects(self, app, client):
        force_login(client, app, "admin@example.com")
        resp = client.get("/deleteUser?email=ghost@example.com", follow_redirects=False)
        assert resp.status_code == 302

    def test_non_admin_cannot_delete_user(self, app, client):
        force_login(client, app, "test@example.com")
        resp = client.get("/deleteUser?email=test@example.com", follow_redirects=False)
        assert resp.status_code in (302, 401)
        # the user must still exist
        with app.app_context():
            assert User.query.filter_by(email="test@example.com").first() is not None


# ===========================================================================
# /logout
# ===========================================================================
class TestLogout:
    def test_logout_requires_auth(self, client):
        resp = client.get("/logout")
        assert resp.status_code in (302, 401)

    def test_logout_redirects_to_login(self, app, client):
        force_login(client, app, "admin@example.com")
        resp = client.get("/logout", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_logout_clears_remember_cookie(self, app, client):
        force_login(client, app, "admin@example.com")
        resp = client.get("/logout", follow_redirects=False)
        # the handler explicitly deletes the remember_token cookie
        set_cookie = resp.headers.get("Set-Cookie", "")
        assert "remember_token" in set_cookie

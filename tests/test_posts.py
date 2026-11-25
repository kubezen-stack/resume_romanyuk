import unittest
from datetime import datetime

from app import create_app, db
from app.posts.models import Post
from app.users.models import User


class PostsBase(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            users = [
                User(username="Max", email="max@example.com", password="test-hash"),
                User(username="Other", email="other@example.com", password="test-hash"),
            ]
            db.session.add_all(users)
            db.session.commit()
            self.user_id = users[0].id
            self.other_user_id = users[1].id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()


class CreatePostTestCase(PostsBase):

    def valid_data(self, **extra):
        data = {"title": "Test post", "content": "Hello", "is_active": "y",
                "publish_date": "2026-11-18T12:30", "category": "tech",
                "author_id": str(self.user_id)}
        data.update(extra)
        return data

    def all_posts(self):
        with self.app.app_context():
            return db.session.scalars(db.select(Post)).all()

    def test_create_form_renders(self):
        response = self.client.get("/post/create")
        self.assertEqual(response.status_code, 200)
        for part in (b'name="title"', b"<textarea", b'rows="5"', b'cols="40"',
                     b'type="checkbox"', b'type="datetime-local"', b"<select", b'type="submit"'):
            self.assertIn(part, response.data)
        self.assertNotIn(b'name="author"', response.data)

    def test_create_post_redirects_and_saves(self):
        response = self.client.post("/post/create", data=self.valid_data())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/post"))
        posts = self.all_posts()
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].title, "Test post")
        self.assertEqual(posts[0].content, "Hello")
        self.assertEqual(posts[0].category, "tech")
        self.assertTrue(posts[0].is_active)
        self.assertEqual(posts[0].posted, datetime(2026, 11, 18, 12, 30))

    def test_create_post_flash_message(self):
        response = self.client.post("/post/create", data=self.valid_data(), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"alert-success", response.data)
        self.assertIn(b"Post added successfully", response.data)

    def test_unchecked_checkbox_saves_inactive_post(self):
        data = self.valid_data()
        del data["is_active"]
        self.client.post("/post/create", data=data)
        self.assertFalse(self.all_posts()[0].is_active)

    def test_author_is_selected_from_database(self):
        response = self.client.post(
            "/post/create", data=self.valid_data(author_id=str(self.other_user_id))
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.all_posts()[0].user_id, self.other_user_id)

    def test_author_is_required_to_create_post(self):
        data = self.valid_data()
        del data["author_id"]
        response = self.client.post("/post/create", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.all_posts(), [])

    def test_invalid_data_is_not_saved(self):
        invalid = [
            self.valid_data(title=""),
            self.valid_data(title="a"),
            self.valid_data(content=""),
            self.valid_data(category=""),
            self.valid_data(category="unknown"),
            self.valid_data(publish_date="not a date"),
            self.valid_data(publish_date=""),
        ]
        for data in invalid:
            response = self.client.post("/post/create", data=data)
            self.assertEqual(response.status_code, 200, data)
            self.assertIn(b"alert-danger", response.data)
            self.assertIn(b"Enter the correct data in the form!", response.data)
        self.assertEqual(self.all_posts(), [])


class PostListTestCase(PostsBase):

    def add_post(self, **kwargs):
        data = {"title": "Title", "content": "Content", "is_active": True,
                "posted": datetime(2026, 1, 1, 12, 0), "user_id": self.user_id}
        data.update(kwargs)
        with self.app.app_context():
            db.session.add(Post(**data))
            db.session.commit()

    def test_empty_list(self):
        response = self.client.get("/post")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"No posts yet", response.data)

    def test_list_ordered_by_date_desc(self):
        self.add_post(title="Oldest", posted=datetime(2026, 1, 1, 10, 0))
        self.add_post(title="Newest", posted=datetime(2026, 3, 1, 10, 0))
        self.add_post(title="Middle", posted=datetime(2026, 2, 1, 10, 0))
        html = self.client.get("/post").data.decode()
        self.assertLess(html.index("Newest"), html.index("Middle"))
        self.assertLess(html.index("Middle"), html.index("Oldest"))

    def test_list_shows_only_visible_posts(self):
        self.add_post(title="Visible post")
        self.add_post(title="Hidden post", is_active=False)
        html = self.client.get("/post").data.decode()
        self.assertIn("Visible post", html)
        self.assertNotIn("Hidden post", html)

    def test_list_shows_category(self):
        self.add_post(title="Tagged", category="tech")
        html = self.client.get("/post").data.decode()
        self.assertIn("tech", html)


class PostDetailTestCase(PostsBase):

    def add_post(self, **kwargs):
        data = {"title": "Detail title", "content": "Detail content", "is_active": True,
                "posted": datetime(2026, 1, 1, 12, 0), "user_id": self.user_id,
                "category": "news"}
        data.update(kwargs)
        with self.app.app_context():
            post = Post(**data)
            db.session.add(post)
            db.session.commit()
            return post.id

    def test_detail_page(self):
        post_id = self.add_post()
        response = self.client.get(f"/post/{post_id}")
        self.assertEqual(response.status_code, 200)
        for text in (b"Detail title", b"Detail content", b"Max", b"news", b"01.01.2026 12:00"):
            self.assertIn(text, response.data)

    def test_detail_of_hidden_post_is_available(self):
        post_id = self.add_post(is_active=False)
        self.assertEqual(self.client.get(f"/post/{post_id}").status_code, 200)

    def test_detail_not_found(self):
        response = self.client.get("/post/999")
        self.assertEqual(response.status_code, 404)
        self.assertIn(b"Page Not Found", response.data)

    def test_list_links_to_detail(self):
        post_id = self.add_post()
        self.assertIn(f'href="/post/{post_id}"'.encode(), self.client.get("/post").data)


class PostUpdateTestCase(PostsBase):

    def add_post(self):
        with self.app.app_context():
            post = Post(title="Old title", content="Old content", is_active=True,
                        posted=datetime(2026, 3, 5, 14, 45), category="news",
                        user_id=self.user_id)
            db.session.add(post)
            db.session.commit()
            return post.id

    def get_post(self, post_id):
        with self.app.app_context():
            return db.session.get(Post, post_id)

    def new_data(self, **extra):
        data = {"title": "New title", "content": "New content", "is_active": "y",
                "publish_date": "2026-12-01T09:15", "category": "tech",
                "author_id": str(self.user_id)}
        data.update(extra)
        return data

    def test_update_form_is_prefilled(self):
        post_id = self.add_post()
        response = self.client.get(f"/post/{post_id}/update")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode()
        self.assertIn('value="Old title"', html)
        self.assertIn("Old content", html)
        self.assertIn('value="2026-03-05T14:45"', html)
        self.assertIn("checked", html)
        self.assertIn('<option selected value="news">', html)

    def test_update_changes_post_and_redirects(self):
        post_id = self.add_post()
        response = self.client.post(f"/post/{post_id}/update", data=self.new_data())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith(f"/post/{post_id}"))
        post = self.get_post(post_id)
        self.assertEqual(post.title, "New title")
        self.assertEqual(post.content, "New content")
        self.assertEqual(post.category, "tech")
        self.assertEqual(post.posted, datetime(2026, 12, 1, 9, 15))
        self.assertEqual(post.user_id, self.user_id)

    def test_update_flash_message(self):
        post_id = self.add_post()
        response = self.client.post(f"/post/{post_id}/update", data=self.new_data(), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"alert-success", response.data)
        self.assertIn("Пост оновлено!".encode(), response.data)

    def test_update_can_deactivate_post(self):
        post_id = self.add_post()
        data = self.new_data()
        del data["is_active"]
        self.client.post(f"/post/{post_id}/update", data=data)
        self.assertFalse(self.get_post(post_id).is_active)

    def test_update_invalid_data_changes_nothing(self):
        post_id = self.add_post()
        response = self.client.post(f"/post/{post_id}/update", data=self.new_data(title="", category=""))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"invalid-feedback", response.data)
        post = self.get_post(post_id)
        self.assertEqual(post.title, "Old title")
        self.assertEqual(post.category, "news")

    def test_update_not_found(self):
        self.assertEqual(self.client.get("/post/999/update").status_code, 404)
        self.assertEqual(self.client.post("/post/999/update", data=self.new_data()).status_code, 404)


class PostDeleteTestCase(PostsBase):

    def add_post(self, title="To delete"):
        with self.app.app_context():
            post = Post(
                title=title,
                content="Content",
                is_active=True,
                posted=datetime(2026, 1, 1),
                user_id=self.user_id,
            )
            db.session.add(post)
            db.session.commit()
            return post.id

    def count_posts(self):
        with self.app.app_context():
            return len(db.session.scalars(db.select(Post)).all())

    def test_get_shows_confirmation_page_and_keeps_post(self):
        post_id = self.add_post()
        response = self.client.get(f"/post/{post_id}/delete")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"To delete", response.data)
        self.assertIn(b'method="post"', response.data)
        self.assertEqual(self.count_posts(), 1)

    def test_post_deletes_and_redirects(self):
        post_id = self.add_post()
        other_id = self.add_post(title="Other")
        response = self.client.post(f"/post/{post_id}/delete")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/post"))
        with self.app.app_context():
            self.assertIsNone(db.session.get(Post, post_id))
            self.assertIsNotNone(db.session.get(Post, other_id))

    def test_delete_flash_message(self):
        post_id = self.add_post()
        response = self.client.post(f"/post/{post_id}/delete", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"alert-success", response.data)
        self.assertIn(b"Post deleted successfully", response.data)

    def test_deleted_post_is_gone(self):
        post_id = self.add_post()
        self.client.post(f"/post/{post_id}/delete")
        self.assertEqual(self.client.get(f"/post/{post_id}").status_code, 404)

    def test_delete_not_found(self):
        self.assertEqual(self.client.get("/post/999/delete").status_code, 404)
        self.assertEqual(self.client.post("/post/999/delete").status_code, 404)


if __name__ == "__main__":
    unittest.main()

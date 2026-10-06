from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from authentication.models import ChildProfile, ParentProfile
from authentication.services import create_child_for_parent

User = get_user_model()


class ChildProfileLanguagePreferenceTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='child_language_test',
            password='testpass123',
            is_child=True,
        )
        self.child = ChildProfile.objects.create(
            user=self.user,
            nickname='LangKid',
            gender='male',
            birth_year=2015,
            language_preference='en',
        )
        self.client.force_authenticate(user=self.user)

    def test_patch_profile_persists_arabic_preference(self):
        response = self.client.patch(
            '/api/auth/profile/child/',
            {'language_preference': 'ar'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.child.refresh_from_db()
        self.assertEqual(self.child.language_preference, 'ar')
        self.assertEqual(response.data['profile']['language_preference'], 'ar')

    def test_child_can_change_own_password(self):
        response = self.client.post(
            '/api/auth/profile/child/password/',
            {'new_password': 'NewStrongPass1!'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewStrongPass1!'))


class CreateChildLanguagePreferenceTests(APITestCase):
    def setUp(self):
        self.parent_user = User.objects.create_user(
            username='parent_language_test',
            password='testpass123',
            is_parent=True,
        )
        self.parent = ParentProfile.objects.create(
            user=self.parent_user,
            name='Parent Language',
        )

    def test_create_child_persists_initial_language_preference(self):
        child = create_child_for_parent(
            self.parent,
            {
                'username': 'arabic_child',
                'password': 'StrongPass1!',
                'nickname': 'ArabicKid',
                'gender': 'female',
                'birth_year': 2016,
                'language_preference': 'ar',
            },
        )

        self.assertEqual(child.language_preference, 'ar')

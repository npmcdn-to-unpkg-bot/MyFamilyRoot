from django.test import TestCase
from custom_user.models import User
from family_tree.models import Person, Relation, Family
from family_tree.models.relation import PARTNERED, RAISED
from family_tree.models.person import ORPHANED_HIERARCHY_SCORE
from django.test.utils import override_settings

@override_settings(SECURE_SSL_REDIRECT=False)
class TestRelationViews(TestCase): # pragma: no cover

    def setUp(self):
        '''
        Creates credientials as all views require login
        '''
        self.family = Family()
        self.family.save()

        self.user = User.objects.create_user(email='prince_barin@flash.com', password='arboria', name='Prince Barin')
        self.user.save()

        self.person = Person(name='Prince Barin', gender='M', user_id = self.user.id, email='prince_barin@flash.com', family_id=self.family.id, hierarchy_score=100)
        self.person.save()

        #http://flashgordon.wikia.com/wiki/Prince_Alan
        self.son = Person(name='Prince Alan', gender='M', family_id=self.family.id, hierarchy_score=-1)
        self.son.save()

        #http://flashgordon.wikia.com/wiki/King_Vultan
        self.vultan = Person(name='King Vultan', gender='M', family_id=self.family.id, hierarchy_score = 200)
        self.vultan.save()

        self.lura = Person(name='Lura', gender='F', family_id=self.family.id)
        self.lura.save()

        self.vultan_junior = Person(name='Vultan Junior', gender='M', family_id=self.family.id)
        self.vultan_junior.save()


    def test_add_relation_view_loads(self):
        '''
        Tests that the add_relation_view loads and uses the correct template
        '''
        self.client.login(email='prince_barin@flash.com', password='arboria')
        response = self.client.get('/add_relation={0}/'.format(self.person.id))
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'family_tree/add_relation.html')


    def test_add_relation_post_rejects_invalid_relation(self):
        '''
        Tests that the add relation api rejects incorrect data
        '''
        self.client.login(email='prince_barin@flash.com', password='arboria')
        response = self.client.post('/add_relation_post={0}/'.format(self.person.id),{'existing_person': '0', 'relation_type': '4',})
        self.assertEqual(404, response.status_code)

    def test_add_relation_post_rejects_invalid_name(self):
        '''
        Tests that the add relation api rejects incorrect data
        '''
        self.client.login(email='prince_barin@flash.com', password='arboria')
        response = self.client.post('/add_relation_post={0}/'.format(self.person.id),{'existing_person': '0', 'relation_type': '1', 'name': ''})
        self.assertEqual(404, response.status_code)

    def test_add_relation_post_rejects_invalid_language(self):
        '''
        Tests that the add relation api rejects incorrect data
        '''
        self.client.login(email='prince_barin@flash.com', password='arboria')
        response = self.client.post('/add_relation_post={0}/'.format(self.person.id),{'existing_person': '0', 'relation_type': '1', 'name': 'Princess Aura', 'language': 'Klingon'})
        self.assertEqual(404, response.status_code)

    def test_add_relation_post_rejects_invalid_gender(self):
        '''
        Tests that the add relation api rejects incorrect data
        '''
        self.client.login(email='prince_barin@flash.com', password='arboria')
        response = self.client.post('/add_relation_post={0}/'.format(self.person.id),{'existing_person': '0', 'relation_type': '1', 'name': 'Princess Aura', 'language': 'en', 'gender': 'W'})
        self.assertEqual(404, response.status_code)

    def test_add_relation_creates_person_and_relation(self):
        '''
        Test that the add relation api correctly creates the right records
        '''
        self.client.login(email='prince_barin@flash.com', password='arboria')
        response = self.client.post('/add_relation_post={0}/'.format(self.person.id),{'existing_person': '0', 'relation_type': '1', 'name': 'Princess Aura', 'language': 'en', 'gender': 'F'})
        self.assertEqual(302, response.status_code)

        aura = Person.objects.get(name = 'Princess Aura')
        self.assertEqual('en', aura.language)
        self.assertEqual('F', aura.gender)
        self.assertEqual(self.family.id, aura.family_id)
        self.assertEqual(100, aura.hierarchy_score)

        relation =Relation.objects.get(from_person_id = aura.id, to_person_id = self.person.id)
        self.assertEqual(1, relation.relation_type)


    def test_add_relation_creates_person_and_relation_with_optional_data(self):
        '''
        Test that the add relation api correctly creates the right records
        '''
        self.client.login(email='prince_barin@flash.com', password='arboria')
        response = self.client.post('/add_relation_post={0}/'.format(self.person.id),{
                                                                            'existing_person': '0',
                                                                            'relation_type': '1',
                                                                            'name': 'Princess Aura',
                                                                            'language': 'en',
                                                                            'gender': 'F',
                                                                            'address': 'Coventry',
                                                                            'birth_year': '1984'})
        self.assertEqual(302, response.status_code)

        aura = Person.objects.get(name = 'Princess Aura')
        self.assertEqual('en', aura.language)
        self.assertEqual('F', aura.gender)
        self.assertEqual('Coventry', aura.address)
        self.assertEqual(1984, aura.birth_year)
        self.assertEqual(self.family.id, aura.family_id)
        self.assertEqual(100, aura.hierarchy_score)

        relation =Relation.objects.get(from_person_id = aura.id, to_person_id = self.person.id)
        self.assertEqual(1, relation.relation_type)


    def test_add_parent_creates_person_and_relation_and_sets_correct_hierarchy(self):
        '''
        Test that the add relation api correctly creates the right records
        '''
        self.client.login(email='prince_barin@flash.com', password='arboria')
        response = self.client.post('/add_relation_post={0}/'.format(self.person.id),{'existing_person': '0', 'relation_type': '3', 'name': 'King Barin', 'language': 'en', 'gender': 'M'})
        self.assertEqual(302, response.status_code)

        king = Person.objects.get(name = 'King Barin')
        self.assertEqual('en', king.language)
        self.assertEqual('M', king.gender)
        self.assertEqual(self.family.id, king.family_id)
        self.assertEqual(99, king.hierarchy_score)

        relation =Relation.objects.get(from_person_id = king.id, to_person_id = self.person.id)
        self.assertEqual(2, relation.relation_type)

    def test_add_relation_to_existing_people(self):
        '''
        Tests that a relation can be added between two existing people sets hierarchy on any missing hierarchy scores
        '''
        self.client.login(email='prince_barin@flash.com', password='arboria')
        response = self.client.post('/add_relation_post={0}/'.format(self.person.id),{'existing_person': '1', 'relation_type': '2', 'relation_id': str(self.son.id)})
        self.assertEqual(302, response.status_code)

        relation =Relation.objects.get(from_person_id = self.person.id, to_person_id = self.son.id)
        self.assertEqual(2, relation.relation_type)

        # reload son
        self.son = Person.objects.get(id=self.son.id)
        self.assertEqual(101, self.son.hierarchy_score)


    def test_break_relation_view_loads(self):
        '''
        Tests that the  break_relation_view loads and uses the correct template
        '''
        relation = Relation(from_person_id=self.vultan.id, to_person_id=self.lura.id,relation_type=PARTNERED)
        relation.save()

        self.client.login(email='prince_barin@flash.com', password='arboria')
        response = self.client.get('/break_relation={0}/'.format(self.vultan.id))
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'family_tree/break_relation.html')
        self.assertEquals(True, b'Lura' in response.content)

    def test_break_relation_post_deletes_relation(self):
        '''
        Tests that the relation is deleted from the post view and check that hierarchy scores set to -1 for
        people with no relations
        '''
        relation = Relation(from_person_id=self.vultan.id, to_person_id=self.lura.id,relation_type=PARTNERED)
        relation.save()

        father_son_relation = Relation(from_person_id=self.vultan.id, to_person_id=self.vultan_junior.id,relation_type=RAISED)
        father_son_relation.save()

        self.client.login(email='prince_barin@flash.com', password='arboria')
        response = self.client.post('/break_relation_post={0}/'.format(self.vultan.id),{'relation_id': relation.id})
        self.assertEqual(302, response.status_code)
        self.assertEqual(0, Relation.objects.filter(from_person_id=self.vultan.id, to_person_id=self.lura.id).count())

        # Reload lura
        self.lura = Person.objects.get(id=self.lura.id)
        self.assertEqual(ORPHANED_HIERARCHY_SCORE, self.lura.hierarchy_score)

        # Reload vultan
        self.vultan = Person.objects.get(id=self.vultan.id)
        self.assertEqual(200, self.vultan.hierarchy_score)


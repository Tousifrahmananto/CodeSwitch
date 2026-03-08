from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from .models import LearningModule, Lesson, Quiz, QuizQuestion, QuizOption

User = get_user_model()


def _make_authed_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.cookies['access_token'] = str(refresh.access_token)
    return client


def create_module_with_lesson():
    """Helper: create a module + lesson (+ quiz) and return them."""
    module = LearningModule.objects.create(
        title='Python Basics',
        description='Learn Python fundamentals.',
        difficulty='beginner',
        language='python',
    )
    lesson = Lesson.objects.create(
        module=module,
        title='Variables',
        content='Variables store data.',
        example_code='x = 1',
        order=1,
    )
    quiz = Quiz.objects.create(lesson=lesson, title='Variables Quiz', passing_score=70)
    question = QuizQuestion.objects.create(quiz=quiz, question_text='What does x = 1 do?', order=1)
    correct = QuizOption.objects.create(question=question, option_text='Assigns 1 to x', is_correct=True)
    wrong = QuizOption.objects.create(question=question, option_text='Prints 1', is_correct=False)
    return module, lesson, quiz, question, correct, wrong


@override_settings(AXES_ENABLED=False)
class ModuleListTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='learn_user', email='learn@example.com', password='Test1234!')
        self.client = _make_authed_client(self.user)
        create_module_with_lesson()

    def test_modules_list_requires_auth(self):
        anon = APIClient()
        response = anon.get('/api/modules')
        self.assertEqual(response.status_code, 401)

    def test_modules_list_returns_data(self):
        response = self.client.get('/api/modules')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Python Basics')

    def test_module_detail(self):
        module = LearningModule.objects.first()
        response = self.client.get(f'/api/modules/{module.id}')
        self.assertEqual(response.status_code, 200)


@override_settings(AXES_ENABLED=False)
class ProgressTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='prog_user', email='prog@example.com', password='Test1234!')
        self.client = _make_authed_client(self.user)
        self.module, self.lesson, *_ = create_module_with_lesson()

    def test_progress_update_marks_lesson_complete(self):
        response = self.client.post('/api/progress/update',
            {'lesson_id': self.lesson.id}, format='json')
        self.assertEqual(response.status_code, 200)
        # Fetch progress and verify lesson is marked complete
        progress_response = self.client.get('/api/progress')
        self.assertEqual(progress_response.status_code, 200)
        self.assertTrue(any(
            p['lesson_id'] == self.lesson.id and p['completed']
            for p in progress_response.data
        ))

    def test_progress_update_idempotent(self):
        """Calling update twice should not error — uses update_or_create."""
        self.client.post('/api/progress/update', {'lesson_id': self.lesson.id}, format='json')
        response = self.client.post('/api/progress/update', {'lesson_id': self.lesson.id}, format='json')
        self.assertIn(response.status_code, [200, 201])

    def test_progress_requires_auth(self):
        anon = APIClient()
        response = anon.post('/api/progress/update', {'lesson_id': self.lesson.id}, format='json')
        self.assertEqual(response.status_code, 401)


@override_settings(AXES_ENABLED=False)
class QuizTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='quiz_user', email='quiz@example.com', password='Test1234!')
        self.client = _make_authed_client(self.user)
        self.module, self.lesson, self.quiz, self.question, self.correct, self.wrong = \
            create_module_with_lesson()

    def test_get_quiz(self):
        response = self.client.get(f'/api/lessons/{self.lesson.id}/quiz/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['title'], 'Variables Quiz')
        self.assertIn('questions', response.data)

    def test_quiz_submit_pass(self):
        response = self.client.post(
            f'/api/quizzes/{self.quiz.id}/submit/',
            {'answers': {str(self.question.id): self.correct.id}},
            format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['passed'])
        self.assertEqual(response.data['score'], 100)

    def test_quiz_submit_fail(self):
        response = self.client.post(
            f'/api/quizzes/{self.quiz.id}/submit/',
            {'answers': {str(self.question.id): self.wrong.id}},
            format='json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['passed'])
        self.assertEqual(response.data['score'], 0)

    def test_quiz_retry_overwrites_previous_attempt(self):
        # First attempt — wrong answer
        self.client.post(
            f'/api/quizzes/{self.quiz.id}/submit/',
            {'answers': {str(self.question.id): self.wrong.id}},
            format='json')
        # Second attempt — correct answer
        response = self.client.post(
            f'/api/quizzes/{self.quiz.id}/submit/',
            {'answers': {str(self.question.id): self.correct.id}},
            format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['passed'])

    def test_quiz_submit_requires_auth(self):
        anon = APIClient()
        response = anon.post(
            f'/api/quizzes/{self.quiz.id}/submit/',
            {'answers': {}},
            format='json')
        self.assertEqual(response.status_code, 401)

    def test_correct_options_revealed_in_response(self):
        response = self.client.post(
            f'/api/quizzes/{self.quiz.id}/submit/',
            {'answers': {str(self.question.id): self.correct.id}},
            format='json')
        self.assertIn('correct_options', response.data)

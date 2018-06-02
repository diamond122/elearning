import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.db.models import Count
from django.core.urlresolvers import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic.edit import CreateView, FormView, UpdateView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.contrib.auth.forms import UserCreationForm
from braces.views import LoginRequiredMixin
from django.contrib.auth import authenticate, login
from students.forms import CourseEnrollForm
from students.forms import StudentSignupForm
from students.forms import StudentInterestsForm
from students.forms import TakeQuizForm
from courses.models import Course
from students.models import Quiz
from students.models import Student
from students.models import TakenQuiz
from students.models import User
from django.core.mail import mail_admins
from django.contrib import messages
from students.decorators import student_required

class StudentCourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'students/course/list.html'

    def get_queryset(self):
        qs = super(StudentCourseListView, self).get_queryset()
        return qs.filter(students__in=[self.request.user])


class StudentCourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'students/course/detail.html'

    def get_queryset(self):
        qs = super(StudentCourseDetailView, self).get_queryset()
        return qs.filter(students__in=[self.request.user])

    def get_context_data(self, **kwargs):
        context = super(StudentCourseDetailView, self).get_context_data(**kwargs)
        course = self.get_object()
        if 'module_id' in self.kwargs:
            #get current module
            context['module'] = course.modules.get(id=self.kwargs['module_id'])
        else:
            #get first module
            context['module'] = course.modules.all()[0]
        context['key'] = settings.STRIPE_LIVE_PUBLIC_KEY
        return context


class StudentRegistrationView(CreateView):
    model = User
    template_name = 'registration/signup_form.html'
    form_class = StudentSignupForm
    success_url = reverse_lazy('student_course_list')

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'student'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        result = super(StudentRegistrationView, self).form_valid(form)
        cd = form.cleaned_data
        user = authenticate(username=cd['username'], password=cd['password1'])
        login(self.request, user)
        return result


class StudentEnrollCourseView(FormView):
    course = None
    form_class = CourseEnrollForm

    def form_valid(self, form):
        self.course = form.cleaned_data['course']
        self.course.students.add(self.request.user)
        return super(StudentEnrollCourseView, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy('student_course_detail', args=[self.course.id])

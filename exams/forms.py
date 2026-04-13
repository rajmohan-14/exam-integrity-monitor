from django import forms
from .models import Exam, Question


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['title', 'duration_mins', 'starts_at', 'trust_threshold', 'shuffle_questions']
        widgets = {
            'starts_at': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'title': forms.TextInput(attrs={'placeholder': 'e.g. Django Midterm Test'}),
            'duration_mins': forms.NumberInput(attrs={'placeholder': '60'}),
            'trust_threshold': forms.NumberInput(attrs={'step': '0.1', 'min': '0', 'max': '1', 'placeholder': '0.5'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['starts_at'].input_formats = ['%Y-%m-%dT%H:%M']


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['body', 'question_type', 'options', 'correct_answer', 'marks']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter your question here...'}),
            'options': forms.Textarea(attrs={'rows': 3, 'placeholder': '{"a": "Option A", "b": "Option B", "c": "Option C", "d": "Option D"}'}),
            'correct_answer': forms.TextInput(attrs={'placeholder': 'e.g. a'}),
        }
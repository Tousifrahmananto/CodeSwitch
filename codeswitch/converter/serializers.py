from rest_framework import serializers

from .models import LANGUAGE_CHOICES, SharedSnippet


class StrictTextField(serializers.CharField):
    def to_internal_value(self, data):
        if not isinstance(data, str):
            self.fail('invalid')
        return super().to_internal_value(data)


class CodeField(StrictTextField):
    def __init__(self, **kwargs):
        super().__init__(trim_whitespace=False, error_messages={
            'max_length': 'Code must be under {max_length:,} characters.'}, **kwargs)

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        if not value.strip():
            self.fail('blank')
        return value


class LanguageField(serializers.ChoiceField):
    def __init__(self):
        super().__init__(choices=LANGUAGE_CHOICES)

    def to_internal_value(self, data):
        if not isinstance(data, str):
            self.fail('invalid_choice', input=data)
        return super().to_internal_value(data.strip().lower())


class ConversionInputSerializer(serializers.Serializer):
    source_language = LanguageField()
    target_language = LanguageField()
    code = CodeField(max_length=50_000)


class ExecutionInputSerializer(serializers.Serializer):
    language = LanguageField()
    code = CodeField(max_length=10_000)
    stdin = StrictTextField(max_length=10_000, allow_blank=True, default='', trim_whitespace=False)


class ExplanationInputSerializer(serializers.Serializer):
    source_language = LanguageField()
    target_language = LanguageField()
    input_code = CodeField(max_length=50_000)
    output_code = CodeField(max_length=50_000)


class VisualizationInputSerializer(serializers.Serializer):
    language = LanguageField()
    code = CodeField(max_length=20_000)


class VerificationInputSerializer(serializers.Serializer):
    source_language = LanguageField()
    target_language = LanguageField()
    source_code = CodeField(max_length=10_000)
    target_code = CodeField(max_length=10_000)
    stdin = StrictTextField(max_length=10_000, allow_blank=True, default='', trim_whitespace=False)

    def validate(self, attrs):
        if attrs['source_language'] == attrs['target_language']:
            raise serializers.ValidationError('Source and target languages must differ.')
        return attrs


class SharedSnippetCreateSerializer(serializers.ModelSerializer):
    source_language = serializers.ChoiceField(choices=LANGUAGE_CHOICES)
    target_language = serializers.ChoiceField(choices=LANGUAGE_CHOICES)
    engine = serializers.ChoiceField(choices=('ai', 'rules'))
    input_code = serializers.CharField(max_length=50_000, trim_whitespace=False)
    output_code = serializers.CharField(max_length=50_000, trim_whitespace=False)

    class Meta:
        model = SharedSnippet
        fields = ('source_language', 'target_language', 'input_code', 'output_code', 'engine')

    def validate(self, attrs):
        if attrs['source_language'] == attrs['target_language']:
            raise serializers.ValidationError('Source and target languages must differ.')
        return attrs

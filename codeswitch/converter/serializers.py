from rest_framework import serializers

from .models import LANGUAGE_CHOICES, SharedSnippet


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

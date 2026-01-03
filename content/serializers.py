from rest_framework import serializers

# Guardrails: limits to prevent abuse and control costs
MAX_SECTION_LENGTH = 10000  # ~2.5k tokens per section
MAX_SECTIONS = 50  # Max sections per page
MAX_TOTAL_CONTENT = 100000  # ~25k tokens total


class PageSectionSerializer(serializers.Serializer):
    type = serializers.CharField(max_length=50)
    text = serializers.CharField(max_length=MAX_SECTION_LENGTH)


class IngestPageSerializer(serializers.Serializer):
    url = serializers.URLField(max_length=2000)
    sections = PageSectionSerializer(many=True)

    def validate_sections(self, sections):
        if len(sections) == 0:
            raise serializers.ValidationError("At least one section is required")

        if len(sections) > MAX_SECTIONS:
            raise serializers.ValidationError(
                f"Too many sections: {len(sections)}. Maximum allowed: {MAX_SECTIONS}"
            )

        total_length = sum(len(s.get("text", "")) for s in sections)
        if total_length > MAX_TOTAL_CONTENT:
            raise serializers.ValidationError(
                f"Total content too large: {total_length} chars. Maximum: {MAX_TOTAL_CONTENT}"
            )

        return sections
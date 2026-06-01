import json
import re
from flask import Flask, render_template, request, jsonify
import anthropic

app = Flask(__name__)
client = anthropic.Anthropic()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate-quiz', methods=['POST'])
def generate_quiz():
    data = request.get_json()
    material = data.get('material', '').strip()
    num_questions = min(max(int(data.get('num_questions', 5)), 2), 10)

    if not material:
        return jsonify({'error': 'Please provide study material'}), 400

    if len(material) < 50:
        return jsonify({'error': 'Please provide more material (at least a paragraph)'}), 400

    prompt = f"""Generate a multiple-choice quiz based on the study material below.
Create exactly {num_questions} questions. Return ONLY valid JSON, no markdown, no explanation.

Format:
{{
  "questions": [
    {{
      "question": "...",
      "options": ["option A text", "option B text", "option C text", "option D text"],
      "correct": 0,
      "explanation": "..."
    }}
  ]
}}

Rules:
- Exactly 4 options per question
- "correct" is the 0-based index of the right answer
- Cover different topics from the material
- Make wrong answers plausible but clearly incorrect

Study Material:
{material}"""

    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.content[0].text.strip()
    if text.startswith('```'):
        text = re.sub(r'^```(?:json)?\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
        text = text.strip()

    quiz_data = json.loads(text)
    if 'questions' not in quiz_data:
        return jsonify({'error': 'Invalid quiz format generated'}), 500

    return jsonify(quiz_data)


if __name__ == '__main__':
    app.run(debug=True, port=5000)

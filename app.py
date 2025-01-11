from flask import Flask, render_template, jsonify
from utils.fantasy_functions import FantasyCalculatorSleeper

app = Flask(__name__)
calculator = FantasyCalculatorSleeper()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/calculate_scores/<player>/<week>')
def calculate_scores(player, week):
    try:
        # Validate week
        week = int(week)
        if week < 1 or week > 17:
            return jsonify({'error': 'Invalid week'}), 400

        if player == 'nolan':
            results = calculator.get_nolan_scores(week)
        elif player == 'pranav':
            results = calculator.get_pranav_scores(week)
        elif player == 'vidy':
            results = calculator.get_vidy_scores(week)
        else:
            return jsonify({'error': 'Invalid player'}), 400
        return jsonify(results)
    except ValueError:
        return jsonify({'error': 'Invalid week format'}), 400
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8000)
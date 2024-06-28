from flask import Flask, render_template, request, redirect, url_for
from scraper import ResumeAnalyzer, setup_database, fetch_all_resumes, DATABASE_FILE

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/match_resumes', methods=['POST'])
def match_resumes():
    job_description = request.form['job_description']
    skills = request.form.getlist('skills[]')
    experiences = request.form.getlist('experiences[]')
    
    # Assuming skills and experiences are used in job_description somehow
    job_description += ' ' + ' '.join(skills) + ' ' + ' '.join(experiences)
    
    analyzer = ResumeAnalyzer(resume_folder='')
    matches = analyzer.find_matching_resumes(job_description)
    
    return render_template('index.html', resumes=matches)

if __name__ == '__main__':
    setup_database()
    app.run(debug=True)
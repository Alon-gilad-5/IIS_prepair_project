import sys
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime
import pytz
import random
import os
from pathlib import Path

# Updated path: relative to app/ocean-test/
# Navigate to project root, then to app/src/data/ocean-test
OCEAN_PATH = Path(__file__).parent.parent / "src" / "data" / "ocean-test"

if __name__ == "__main__":
    st.set_page_config(page_title="Personality Test", page_icon="🎨", layout="wide")

# Custom CSS
st.markdown("""
<style>
    /* Global Styling */
    :root {
        --primary-color: #2c3e50;      /* Deep navy blue */
        --secondary-color: #3498db;    /* Bright blue */
        --accent-color: #2ecc71;       /* Soft green */
        --background-color: #f4f6f8;   /* Light gray-blue */
        --text-color: #2c3e50;         /* Dark gray */
    }

    /* Base App Styling */
    .stApp {
        background-color: var(--background-color);
        font-family: 'Inter', 'Segoe UI', Roboto, sans-serif;
    }

    /* Title Styling */
    .stTitle {
        color: var(--primary-color);
        font-weight: 700;
        text-align: center;
        margin-bottom: 30px;
    }

    /* Button Styling */
    .stButton > button {
        background-color: var(--secondary-color);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    .stButton > button:hover {
        background-color: var(--primary-color);
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(0,0,0,0.15);
    }

    /* Card-like Containers */
    .stContainer {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
    }

    .stContainer:hover {
        transform: scale(1.02);
        box-shadow: 0 12px 25px rgba(0,0,0,0.12);
    }

    /* Radio Button Styling */
    .stRadio > div {
        background-color: white;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# Define choices structure
CHOICES = {
    "plus": [
        {"text": "Very Inaccurate", "score": 1},
        {"text": "Moderately Inaccurate", "score": 2},
        {"text": "Neither Accurate Nor Inaccurate", "score": 3},
        {"text": "Moderately Accurate", "score": 4},
        {"text": "Very Accurate", "score": 5}
    ],
    "minus": [
        {"text": "Very Inaccurate", "score": 5},
        {"text": "Moderately Inaccurate", "score": 4},
        {"text": "Neither Accurate Nor Inaccurate", "score": 3},
        {"text": "Moderately Accurate", "score": 2},
        {"text": "Very Accurate", "score": 1}
    ]
}

class IPIPNeoTest:
    def __init__(self):
        self.domains = {
            'N': 'Neuroticism',
            'E': 'Extraversion',
            'O': 'Openness To Experience',
            'A': 'Agreeableness',
            'C': 'Conscientiousness'
        }
        
        # Load questions and domain descriptions
        with open(OCEAN_PATH / "questions_ipip_neo_120.json", 'r') as f:
            self.questions = json.load(f)
            
        with open(OCEAN_PATH / "get-template-en.json", 'r') as f:
            self.domain_info = json.load(f)
    
    def get_score_for_response(self, response_text, keyed):
        """Get numerical score based on response text and question keying"""
        choices = CHOICES[keyed]
        for choice in choices:
            if choice["text"] == response_text:
                return choice["score"]
        return None
    
    def calculate_scores(self, responses):
        """Calculate domain and facet scores using the specified scoring system"""
        scores = {domain: {'total': 0, 'facets': {}} for domain in self.domains}
        
        for q_id, response in responses.items():
            question = next(q for q in self.questions if q['id'] == q_id)
            
            # Get score based on response text and question keying
            score = self.get_score_for_response(response, question['keyed'])
            
            domain = question['domain']
            facet = question['facet']
            
            # Initialize facet if needed
            if facet not in scores[domain]['facets']:
                scores[domain]['facets'][facet] = []
            
            # Add score to appropriate domain and facet
            scores[domain]['facets'][facet].append(score)
            scores[domain]['total'] += score
        
        # Calculate averages
        for domain in scores:
            # Average domain score
            scores[domain]['total'] /= len([q for q in self.questions if q['domain'] == domain])
            
            # Average facet scores
            for facet in scores[domain]['facets']:
                scores[domain]['facets'][facet] = sum(scores[domain]['facets'][facet]) / len(scores[domain]['facets'][facet])
        
        return scores

    def get_interpretation(self, domain_scores):
        """Get text interpretations for each domain score"""
        interpretations = {}
        
        for domain_code, score in domain_scores.items():
            domain_info = next(d for d in self.domain_info if d['domain'] == domain_code)
            
            # Determine score level
            if score['total'] < 2.7:
                level = 'low'
            elif score['total'] > 3.2:
                level = 'high'
            else:
                level = 'neutral'
            
            # Get corresponding interpretation text
            interpretation = next(r for r in domain_info['results'] if r['score'] == level)
            interpretations[domain_code] = {
                'text': interpretation['text'],
                'description': domain_info['description'],
                'facets': domain_info['facets']
            }
        
        return interpretations

    def create_visualizations(self, scores):
        """Create visualizations of the results"""
        # Radar chart of domain scores
        domain_scores = {self.domains[d]: scores[d]['total'] for d in scores}
        
        fig_radar = go.Figure(data=go.Scatterpolar(
            r=list(domain_scores.values()),
            theta=list(domain_scores.keys()),
            fill='toself'
        ))
        
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[1, 5])),
            showlegend=False,
            title="Your Personality Profile Based on IPIP-NEO-120"
        )
        
        # Facet breakdown charts
        facet_figs = {}
        for domain in scores:
            facet_scores = scores[domain]['facets']

            # Get the facet titles
            domain_facets = next(d for d in self.domain_info if d['domain'] == domain)['facets']

            df_facets = pd.DataFrame({
                'Facet': [facet['title'] for facet in domain_facets],
                'Score': list(facet_scores.values())
            })
        
            fig_facets = px.bar(
                df_facets,
                x='Facet',
                y='Score',
                title=f"{self.domains[domain]} - Facets",
                color='Score',
                color_continuous_scale='RdYlBu'
            )

            fig_facets.update_layout(
                yaxis=dict(range=[0, 5]),
                coloraxis=dict(cmin=0, cmax=5)
                )

            facet_figs[domain] = fig_facets
        
        return fig_radar, facet_figs

# Engaging introduction
def show_welcome_screen():
    st.title("Unlock Your Professional Potential 🎨")
    st.markdown("""
    ### Personality Insights for Career Success

    Discover the unique qualities that set you apart in the workplace.

    This evidence-based assessment provides:
    - Precise insights into your professional personality
    - Strategic understanding of your workplace strengths
    - A scientific approach to personal and professional growth

    **Your Pathway to Professional Self-Awareness** 🚀
    """)

    if st.button("Start Assessment", key="start_test"):
        st.session_state.show_welcome = False


def feedback_form():
    st.subheader("Feedback Form")
    st.write("We appreciate your feedback! Please answer the following questions:")

    quality = st.radio("How helpful did you find the OCEAN test for understanding your personality traits? (1-5)",
                       ["1", "2", "3", "4", "5"], index=4)
    relevance = st.radio(
        "Did the personality test results give you valuable insights into your strengths? (Yes, No, Somewhat)",
        ["Yes", "No", "Somewhat"], index=0)
    alignment = st.radio("Would you recommend the personality test to others preparing for interviews? (Yes, No)",
                         ["Yes", "No"], index=0)
    use_again = st.radio("Would you use this simulator again for future job interviews?", ["Yes", "No", "Maybe"],
                         index=0)
    suggestions = st.text_area("Do you have any additional comments or suggestions for improving the personality test?")

    if st.button("Submit Feedback"):
        st.success("Thank you for your feedback!")
        st.session_state.stage = "completed"
        st.rerun()

def main():
    # Initialize welcome screen state
    if 'show_welcome' not in st.session_state:
        st.session_state.show_welcome = True

    # Initialize stage state
    if 'stage' not in st.session_state:
        st.session_state.stage = "welcome"

    # Show welcome screen or test
    if st.session_state.stage == "welcome":
        if st.session_state.show_welcome:
            show_welcome_screen()
        else:
            st.session_state.stage = "test"
            st.rerun()

    elif st.session_state.stage == "test":
        st.title("IPIP-NEO-120 Personality Assessment")

        # Initialize session state
        if 'test' not in st.session_state:
            st.session_state.test = IPIPNeoTest()
            st.session_state.current_question = 0
            st.session_state.responses = {}
            st.session_state.test_complete = False
            random.seed(42)
            st.session_state.questions = list(st.session_state.test.questions)
            random.shuffle(st.session_state.questions)

        if not st.session_state.test_complete:
            # Display progress
            progress = len(st.session_state.responses) / len(st.session_state.questions)
            st.progress(progress)
            st.write(f"Question {len(st.session_state.responses) + 1} of {len(st.session_state.questions)}")

            # Display current question
            current_q = st.session_state.questions[st.session_state.current_question]
            st.write(f"**{current_q['text']}**")

            # Get choices based on question keying
            choices = [choice["text"] for choice in CHOICES[current_q['keyed']]]

            # Create radio buttons for choices
            response = st.radio("Select your answer:", choices, key=f"q_{current_q['id']}")

            # Next button
            if st.button("Next"):
                if response != "Select an answer":
                    st.session_state.responses[current_q['id']] = response

                    if st.session_state.current_question < len(st.session_state.questions) - 1:
                        st.session_state.current_question += 1
                        st.rerun()
                    else:
                        st.session_state.test_complete = True
                        st.rerun()
                else:
                    st.warning("Please select an answer before proceeding.")

        else:
            # Calculate and display results
            scores = st.session_state.test.calculate_scores(st.session_state.responses)
            interpretations = st.session_state.test.get_interpretation(scores)
            radar_fig, facet_figs = st.session_state.test.create_visualizations(scores)

            st.write("## Your Results")

            # Display radar chart
            st.plotly_chart(radar_fig, use_container_width=True)

            # Display detailed results for each domain
            for domain_code, domain_name in st.session_state.test.domains.items():
                with st.expander(f"{domain_name} Details"):
                    st.plotly_chart(facet_figs[domain_code], use_container_width=True)
                    st.write("---")
                    st.write("### Interpretation")
                    st.write(interpretations[domain_code]['text'])
                    st.write("---")
                    st.write("### Domain Description")
                    st.write(interpretations[domain_code]['description'])
                    st.write("---")
                    st.write("### Facet Details")
                    for facet in interpretations[domain_code]['facets']:
                        st.write(f"**{facet['title']}:** {facet['text']}")

            # Save results
            if st.button("Save Results"):
                israel_tz = pytz.timezone('Asia/Jerusalem')
                results = {
                    'timestamp': datetime.now(israel_tz).isoformat(),
                    'domain_scores': {d: scores[d]['total'] for d in scores},
                    'facet_scores': {d: scores[d]['facets'] for d in scores},
                    'interpretations': interpretations
                }

                os.makedirs(OCEAN_PATH, exist_ok=True)
                results_file = OCEAN_PATH / "ipip_neo_results.json"

                with open(results_file, "w") as f:
                    json.dump(results, f, indent=2)

                st.success(f"Results have been saved successfully! ✨")
                st.session_state.stage = "feedback"
                st.rerun()
    # Ask user for feedback
    elif st.session_state.stage == "feedback":
        feedback_form()

    elif st.session_state.stage == "completed":
        st.success("Thank you for completing the personality test and providing feedback! 🎉")
        if st.button("Start New Test"):
            # Reset all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()

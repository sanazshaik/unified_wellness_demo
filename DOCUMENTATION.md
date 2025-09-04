# Case Study Documentation: Unified Wellness Dashboard

## 1. Overview

The **Unified Wellness Dashboard** was designed to address the challenge of fragmented health data across multiple sources. By consolidating sleep, nutrition, fitness activity, and biometrics into a single secure platform, the dashboard empowers users to make informed lifestyle choices. The focus is on delivering actionable insights, strong security, and AI-driven personalization.

I chose **Groq + LLaMA** over other AI solutions because of Groq’s high performance in running LLMs at scale with low latency, which is crucial for real-time insights. I chose **Streamlit and SQLite** for rapid prototyping and ease of integration. Streamlit allowed me to deliver a functional, interactive UI quickly, while SQLite provided a lightweight database suitable for secure local storage. For long-term scalability, the design can be migrated to **React + cloud databases** for better performance and scalability.

To simulate realistic input, I generated synthetic but relevant data for sleep, nutrition, activity, and biometrics. This ensured the dashboard could demonstrate real-world scenarios without relying on sensitive user datasets - and also for the sake of time.

---

## 2. Success Metrics

* **Actionable Insights**: Personalized recommendations that help users make better health choices.
    * I adhered to clear documentation standards (inline comments, docstrings, and usage examples) - making it easy for others to understand how insights were generated and ensured reproducibility.
* **Data Unification**: Integration of multiple disparate sources into one coherent dashboard.
    * I followed integration documentation for APIs, CSVs, and database connectors, carefully noting data formats and preprocessing steps. I documented pipeline flow to ensure consistency when merging disparate data sources.
* **Holistic View**: A complete story of wellness rather than disjointed numbers.
    * Documentation made it clear how the system produced a full wellness picture instead of fragmented metrics. I incorporated a wellness summary, text captions, insights, reccommendations, AI Chatbot, and data visualization to convey meaningful insight and visual appeal.
* **AI Application**: Effective use of anomaly detection, correlations, and AI coaching.
    * I implemented anomaly detection and correlation methods while citing algorithms and parameter choices in the documentation. This made the AI components easy to validate.

---

## 3. Requirements & Constraints

* **Requirements**:

  * Secure user authentication and 2FA.
  * Unified data visualization
  * AI-powered insights and anomaly detection.
  * User-friendly design adaptable for target audiences.
* **Constraints**:

  * Prototype limited to CSVs and local DB.
  * Limited resources for large-scale ML training.
  * Responsibly handle healtcare-related data.

---

## 4. Methodology

1. **Define Problem** – Identified fragmentation of health data as the core issue.
2. **Design Thinking** – Created Figma mockups of a “story dashboard” to visualize data narratively.

   * [Figma Storyboard – Unified Wellness](https://www.figma.com/board/GHHyEl92nq2UPEX8Zxkltr/Storyboard---Unified-Wellness?node-id=0-1&t=HdyxFIpfKVAlvWbH-1)
   * Design rationale: storytelling builds user engagement by showing cause-effect (e.g., poor sleep → fatigue).
3. **Rapid Prototyping** – Built core dashboard in Streamlit with SQLite.
4. **Synthetic Data Generation** – Created relevant synthetic datasets to simulate real-world patterns for sleep, nutrition, and activity while avoiding sensitive healthcare data.
5. **AI Integration** – Used Groq + LLaMA for AI, and assistance from OpenAI for prompt engineering to generate structured, efficient code.
6. **Testing** – Iterative process. Validated anomalies, correlations, and UI functionality.

---

## 5. Features

1. **User Authentication** – Secure login with hashed passwords.
2. **Google Authenticator 2FA** – pyotp + qrcode for MFA.
3. **Unified Dashboard** – Sleep, physical activity, calories, hydration, nutrition, biometrics in one view.
4. **Customizable Goals** – Steps, macros, water intake.
5. **AI Health Coach** – Groq + LLaMA backend for recommendations.
6. **Anomaly Detection** – Z-score and EWM statistical detection.
7. **Data Visualization** – Altair, Pandas, NumPy for trends and correlations.
8. **Personalization** – Targeted for fitness enthusiasts, health-conscious users, and users with chronic condition.
9. **API Support** – Extensible to Fitbit, Google Fit, and Apple HealthKit, etc.

---

## 6. Responsible AI Concerns & Ethics

* **Bias**: Ensure recommendations are not skewed by incomplete data.
* **User Control**: Users control their own data inputs and goal settings.
* **Ethics**: Avoid overstating health recommendations; clarify limitations. Clear logs so it doesn't travel to backend such as encrypting AI Logs but are only visible to the user. Adopting enhanced security measures will ensure the platform remains ethical and impactful for sensitive healthcare applications.

---

## 7. Security Features & Importance

* **MFA with Google Authenticator**: Reduces account takeover risk.
* **Local Encrypted Data**: SQLite prevents exposure during transit
* **Access Control**: Users only access their personal data.
* **Why**: Healthcare data is highly sensitive; therefore, any breach risks trust and regulatory non-compliance.

**Future Security Enhancements:**

* End-to-end encryption.
* Role-based access control.
* Compliance with HIPAA/GDPR standards.
* Secure API calls
* Consent to data sharing or to keep privacy

---

## 8. Future Enhancements

* **API Integrations**: Apple HealthKit, Google Fit, MyFitnessPal.
* **Scalability**: Migrate frontend to React and backend to cloud-hosted DB.
* **Advanced AI**: Use machine learning methods such as Isolation Forests or GBM/XGBoost for predictive modeling.
* **Data Privacy**: Full encryption and secure cloud deployment.
* **Interactivity**: Add progress sharing.
* **Bug Fixes**: Address minor issues in the prototype.
* **Detailed Documentation**: Add more detailed explanations of function parameters and function descriptions for readability and maintainability


---

## 9. Possible Risks

* **Data Breach**: Healthcare data exposure which can be mitigated with encryption and MFA.
* **Overreliance on AI**: Users misinterpreting insights as medical advice → mitigated with disclaimers. Not doctor-approved.
* **Scalability**: Streamlit may limit enterprise selection which can be fixed with migration.
* **Synthetic Data**: Okay for prototypes, but synthetic data may miss nuances of real-world healthcare data when developing statistics or valuable insights.

---

## 10. References
* [Groq API Documentation](https://console.groq.com/docs/overview)
* [Streamlit Official Docs](https://docs.streamlit.io/)
* [SQLite](https://sqlite.org/)
* [Figma Storyboard – Unified Wellness](https://www.figma.com/board/GHHyEl92nq2UPEX8Zxkltr/Storyboard---Unified-Wellness?node-id=0-1&t=HdyxFIpfKVAlvWbH-1)

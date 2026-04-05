#  Campus Micro-Gig Board

A student-to-student campus gig marketplace built for WebFusion 2026 Prelims.

**Built by:** Mohammad Shahwaz Alam, Suryansh Dev & Pratiksha Chakraborty  
**Course:** B.Tech CSE 2nd Year

---

## How to Run

```bash
pip install -r requirements.txt
python flaskfile.py
```

Open http://127.0.0.1:5000 in your browser.

Deployed Link: https://statuesque-puffpuff-36c637.netlify.app/

---

##  Project Structure

```
campus_gig_board/
├── flaskfile.py          ← Flask app (all routes)
├── models.py             ← SQLAlchemy DB models
├── requirements.txt      ← Dependencies
├── static/
│   └── styles.css        ← Scrapbook UI styles
└── templates/
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── gig_detail.html
    ├── apply.html
    ├── applicants.html
    ├── my_gigs.html
    ├── my_applications.html
    ├── notifications.html
    ├── leaderboard.html
    ├── profile.html
    ├── success.html
    ├── help.html
    └── about.html
```

---

## Features

-  Post gigs with bounty starting ₹50
-  Live gig feed with category filters
-  Full gig status system: Open → Applied → In Progress → Done
-  Applicant management for gig posters
-  My Applications — track every gig you applied to
-  My Gigs — manage all gigs you posted
-  Real-time notifications (apply, accept, reject, completion)
-  Leaderboard — top earners, workers, posters
-  UPI QR code payment system on profiles
-  Student profiles with skills, bio, earnings
-  Help/FAQ page with accordion
-  SQLite database (auto-created on first run)

---

##  Tech Stack

- **Backend:** Python, Flask, SQLAlchemy
- **Frontend:** HTML5, CSS3, Jinja2
- **Database:** SQLite

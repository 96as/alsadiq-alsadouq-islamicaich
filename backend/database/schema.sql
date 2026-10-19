DROP TABLE IF EXISTS Usage;
DROP TABLE IF EXISTS MoralData;
DROP TABLE IF EXISTS Report;
DROP TABLE IF EXISTS Alerts;
DROP TABLE IF EXISTS Conversations;
DROP TABLE IF EXISTS Gamification;
DROP TABLE IF EXISTS Session_Info;
DROP TABLE IF EXISTS Avatar;
DROP TABLE IF EXISTS Linkage;
DROP TABLE IF EXISTS Child;
DROP TABLE IF EXISTS Parent;

CREATE TABLE Parent (
    parent_id SERIAL PRIMARY KEY,
    parent_name VARCHAR(100) NOT NULL,
    parent_email VARCHAR(255) NOT NULL UNIQUE,
    parent_phone VARCHAR(20),
    parent_birth_year INTEGER,
    parent_password_hash VARCHAR(255) NOT NULL
);

CREATE TABLE Child (
    child_id SERIAL PRIMARY KEY,
    child_nickname VARCHAR(50) NOT NULL,
    child_gender VARCHAR(20),
    child_email VARCHAR(255),
    child_birth_year INTEGER,
    child_current_level INTEGER DEFAULT 1,
    child_avatar_visible BOOLEAN DEFAULT TRUE
);

CREATE TABLE Linkage (
    link_id SERIAL PRIMARY KEY,
    parent_id INTEGER NOT NULL,
    child_id INTEGER NOT NULL,
    consent_status VARCHAR(50) DEFAULT 'pending',
    date_linked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    memory TEXT,
    FOREIGN KEY (parent_id) REFERENCES Parent(parent_id) ON DELETE CASCADE,
    FOREIGN KEY (child_id) REFERENCES Child(child_id) ON DELETE CASCADE
);

CREATE TABLE Avatar (
    avatar_id SERIAL PRIMARY KEY,
    child_id INTEGER NOT NULL,
    emotion_state VARCHAR(50) DEFAULT 'neutral',
    lip_sync_status VARCHAR(50) DEFAULT 'idle',
    FOREIGN KEY (child_id) REFERENCES Child(child_id) ON DELETE CASCADE
);

CREATE TABLE Gamification (
    game_id SERIAL PRIMARY KEY,
    child_id INTEGER NOT NULL,
    badge_awarded VARCHAR(100),
    quest_id VARCHAR(100),
    points INTEGER DEFAULT 0,
    completion_status VARCHAR(50) DEFAULT 'in_progress',
    story_id INTEGER,
    FOREIGN KEY (child_id) REFERENCES Child(child_id) ON DELETE CASCADE
);

CREATE TABLE Session_Info (
    session_id SERIAL PRIMARY KEY,
    child_id INTEGER NOT NULL,
    mood_state VARCHAR(50),
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    duration INTERVAL,
    FOREIGN KEY (child_id) REFERENCES Child(child_id) ON DELETE CASCADE
);

CREATE TABLE Alerts (
    alert_id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL,
    parent_id INTEGER NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    alert_description TEXT,
    FOREIGN KEY (session_id) REFERENCES Session_Info(session_id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES Parent(parent_id) ON DELETE CASCADE
);

CREATE TABLE Conversations (
    conversation_id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL,
    text_input TEXT,
    voice_input TEXT,
    language_set VARCHAR(20) DEFAULT 'en',
    conversation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES Session_Info(session_id) ON DELETE CASCADE
);

CREATE TABLE MoralData (
    dataset_id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL,
    moral_focus VARCHAR(100),
    hadith_reference VARCHAR(255),
    quran_reference VARCHAR(255),
    safety_filter_flag BOOLEAN DEFAULT FALSE,
    story_source VARCHAR(255),
    FOREIGN KEY (conversation_id) REFERENCES Conversations(conversation_id) ON DELETE CASCADE
);

CREATE TABLE Report (
    report_id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL,
    parent_id INTEGER NOT NULL,
    dataset_id INTEGER,
    honesty_score REAL,
    insight_summary TEXT,
    emotional_tone VARCHAR(50),
    recommendations TEXT,
    FOREIGN KEY (session_id) REFERENCES Session_Info(session_id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES Parent(parent_id) ON DELETE CASCADE,
    FOREIGN KEY (dataset_id) REFERENCES MoralData(dataset_id) ON DELETE SET NULL
);

CREATE TABLE Usage (
    usage_id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES Conversations(conversation_id) ON DELETE CASCADE
);

CREATE INDEX idx_linkage_parent ON Linkage(parent_id);
CREATE INDEX idx_linkage_child ON Linkage(child_id);
CREATE INDEX idx_avatar_child ON Avatar(child_id);
CREATE INDEX idx_gamification_child ON Gamification(child_id);
CREATE INDEX idx_session_child ON Session_Info(child_id);
CREATE INDEX idx_alerts_session ON Alerts(session_id);
CREATE INDEX idx_alerts_parent ON Alerts(parent_id);
CREATE INDEX idx_conversations_session ON Conversations(session_id);
CREATE INDEX idx_moraldata_conversation ON MoralData(conversation_id);
CREATE INDEX idx_report_session ON Report(session_id);
CREATE INDEX idx_report_parent ON Report(parent_id);
CREATE INDEX idx_usage_conversation ON Usage(conversation_id);
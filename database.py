import mysql.connector

# Databasekonfigurationer
DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "sugrp204",
    "password": "F25-20-100-x20",
    "database": "sugrp204",
    "port": 3306
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as e:
        print(f"Error connecting to MySQL: {e}")
        raise

def setup_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Tabel: Brugere
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            cpr_nummer VARCHAR(20) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL
        );
        """)

        # Tabel: Konsultationsbesvarelser
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS akne_konsultation (
            id INT AUTO_INCREMENT PRIMARY KEY,
            patient_id INT NOT NULL,

            status VARCHAR(50),
            kommentar1 TEXT,

            bivirkninger VARCHAR(50),
            kommentar2 TEXT,

            medicin VARCHAR(50),
            kommentar3 TEXT,

            gener INT,
            kommentar4 TEXT,

            symptomer VARCHAR(50),
            kommentar5 TEXT,

            pande BOOLEAN DEFAULT FALSE,
            kinder BOOLEAN DEFAULT FALSE,
            hage BOOLEAN DEFAULT FALSE,
            bryst BOOLEAN DEFAULT FALSE,
            ryg BOOLEAN DEFAULT FALSE,
            kommentar6 TEXT,

            feedback VARCHAR(10),
            kommentar7 TEXT,

            billede_navn VARCHAR(255),
            oprettet_tidspunkt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (patient_id) REFERENCES patient_users(id) ON DELETE CASCADE
        );
        """)

        # Tabel: Påkrævede konsultationer
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS paakraevet_konsultation (
            id INT AUTO_INCREMENT PRIMARY KEY,
            patient_id INT NOT NULL,
            deadline DATETIME NOT NULL,
            oprettet_af_laege TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            besvaret BOOLEAN DEFAULT FALSE,

            FOREIGN KEY (patient_id) REFERENCES patient_users(id) ON DELETE CASCADE
        );
        """)

        conn.commit()
        print("✅ Alle tabeller er oprettet korrekt.")
    except mysql.connector.Error as e:
        print(f"❌ Fejl ved oprettelse af tabeller: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    setup_database()

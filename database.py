import mariadb

# Databasekonfigurationer
DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "sugrp204",
    "password": "F25-20-100-x20",
    "database": "patient_konsulation",
    "port": 3306
}

def get_db_connection():
    try:
        conn = mariadb.connect(**DB_CONFIG)
        return conn
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB: {e}")
        raise

def setup_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Opret patient-login-tabellen
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            cpr_nummer VARCHAR(20) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL
        );
        """)

        # Opret konsultationsbesvarelser
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
        conn.commit()
        print("Databasen og tabellerne er oprettet.")
    except mariadb.Error as e:
        print(f"Error creating tables: {e}")
    finally:
        cursor.close()
        conn.close()

# Kør funktionen
if __name__ == "__main__":
    setup_database()

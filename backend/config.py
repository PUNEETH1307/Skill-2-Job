import os


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_TOKEN_EXPIRY_MINUTES = int(os.environ.get('JWT_TOKEN_EXPIRY_MINUTES', 30))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SPACY_MODEL = os.environ.get('SPACY_MODEL', 'en_core_web_sm')
    UPLOAD_FOLDER = os.environ.get(
        'UPLOAD_FOLDER',
        os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
    )
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB upload limit
    ALLOWED_RESUME_EXTENSIONS = {'pdf', 'docx'}


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'mysql+pymysql://root:PUNEE13%40work@127.0.0.1:3306/skillbridge'
    )


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    JWT_SECRET_KEY = 'test-jwt-secret-key'
    SECRET_KEY = 'test-secret-key'


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        url = os.environ.get('DATABASE_URL', '')
        # Aiven MySQL URLs sometimes use 'mysql://' — ensure pymysql driver
        if url.startswith('mysql://'):
            url = url.replace('mysql://', 'mysql+pymysql://', 1)
        return url


config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}

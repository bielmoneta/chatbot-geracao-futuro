# database.py

from sqlalchemy import create_engine, Column, Integer, String, Float, BigInteger, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
import datetime

# Cria a base para nossos modelos (tabelas)
Base = declarative_base()

# Define a URL do banco de dados (será um arquivo chamado 'geracao_futuro.db' na mesma pasta)
DATABASE_URL = "sqlite:///geracao_futuro.db"

# Configura o motor do banco de dados
engine = create_engine(DATABASE_URL)

# Cria uma "fábrica" de sessões para interagir com o banco
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- MODELOS (CLASSES QUE REPRESENTAM AS TABELAS) ---

class PontoFocal(Base):
    """Representa uma instituição (escola, empresa) que é um ponto de coleta."""
    __tablename__ = 'pontos_focais'
    
    id = Column(Integer, primary_key=True, index=True)
    id_campanha = Column(String, unique=True, nullable=False, index=True)
    nome_instituicao = Column(String, nullable=False)
    nome_responsavel = Column(String, nullable=False)
    admin_telegram_id = Column(BigInteger, unique=True, nullable=False)
    litros_validados = Column(Float, default=0.0)

    # Relacionamento: Um PontoFocal pode ter vários Geradores
    geradores = relationship("Gerador", back_populates="ponto_focal")

class Gerador(Base):
    """Representa um usuário doador de óleo."""
    __tablename__ = 'geradores'
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    nome_usuario = Column(String)
    ponto_focal_id = Column(Integer, ForeignKey('pontos_focais.id'))

    # Relacionamento inverso: Um Gerador pertence a um PontoFocal
    ponto_focal = relationship("PontoFocal", back_populates="geradores")
    # Relacionamento: Um Gerador pode ter várias Doações
    doacoes = relationship("Doacao", back_populates="gerador")


class Doacao(Base):
    """Representa o registro de uma entrega de óleo."""
    __tablename__ = 'doacoes'
    
    id = Column(Integer, primary_key=True, index=True)
    id_entrega = Column(String, unique=True, nullable=False, index=True)
    gerador_id = Column(Integer, ForeignKey('geradores.id'))
    litros_informados = Column(Float, nullable=False)
    status = Column(String, nullable=False, default='pendente')  # Status: 'pendente' ou 'validado'
    data_criacao = Column(DateTime, default=datetime.datetime.utcnow)

    # Relacionamento inverso: Uma Doação pertence a um Gerador
    gerador = relationship("Gerador", back_populates="doacoes")


def criar_banco():
    """Cria o arquivo do banco de dados e todas as tabelas, se não existirem."""
    print("Criando banco de dados e tabelas, se necessário...")
    Base.metadata.create_all(bind=engine)
    print("Banco de dados pronto.")
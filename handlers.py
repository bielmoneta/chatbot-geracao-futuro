# handlers.py

import logging
import random
import string
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from database import SessionLocal, PontoFocal, Gerador, Doacao

# Configura o logging para vermos os erros
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Estados da Conversa para Cadastro de Ponto Focal ---
(NOME_INSTITUICAO, NOME_RESPONSAVEL, ID_CAMPANHA) = range(3)

# --- Estados da Conversa para Registro de Doação ---
(CODIGO_ASSOCIAR, QUANTIDADE_LITROS) = range(3, 5)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Função inicial chamada com o comando /start."""
    user = update.effective_user
    db = SessionLocal()
    try:
        # Verifica se o usuário já é um Ponto Focal
        ponto_focal = db.query(PontoFocal).filter(PontoFocal.admin_telegram_id == user.id).first()
        if ponto_focal:
            await update.message.reply_text(
                f"Olá, {ponto_focal.nome_responsavel}! Você é o admin do ponto de coleta '{ponto_focal.nome_instituicao}'.\n"
                "Use /validar <código> para validar uma entrega ou /placar para ver o total arrecadado."
            )
            return

        # Verifica se o usuário já é um Gerador
        gerador = db.query(Gerador).filter(Gerador.telegram_id == user.id).first()
        if gerador:
            await update.message.reply_text(
                f"Olá de novo, {user.first_name}! Bem-vindo(a) de volta ao Geração Futuro.\n"
                "Use /doar para registrar uma nova entrega de óleo ou /placar para ver o resultado da sua campanha."
            )
            return

        # Se for um usuário totalmente novo
        await update.message.reply_text(
            f"Olá, {user.first_name}! 👋 Bem-vindo(a) ao Geração Futuro.\n\n"
            "Eu ajudo a organizar a coleta de óleo de cozinha usado para apoiar projetos para jovens.\n\n"
            "O que você gostaria de fazer?\n"
            "➡️ Para participar de uma campanha e doar seu óleo, use o comando /participar.\n"
            "➡️ Se você é responsável por uma instituição (escola, empresa) e quer se tornar um ponto de coleta, use /cadastrar_local."
        )
    finally:
        db.close()


# --- FLUXO DE CADASTRO DE PONTO FOCAL ---

async def cadastrar_local_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia o fluxo de cadastro de um novo Ponto Focal."""
    await update.message.reply_text("Ótimo! Vamos cadastrar sua instituição como um Ponto de Coleta.\nQual o nome da instituição (escola, empresa, etc)?")
    return NOME_INSTITUICAO

async def receber_nome_instituicao(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe o nome da instituição e pede o nome do responsável."""
    context.user_data['nome_instituicao'] = update.message.text
    await update.message.reply_text(f"Entendido. E qual o seu nome (responsável pelo ponto de coleta)?")
    return NOME_RESPONSAVEL

async def receber_nome_responsavel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe o nome do responsável e pede um código para a campanha."""
    context.user_data['nome_responsavel'] = update.message.text
    await update.message.reply_text("Perfeito. Agora, crie um CÓDIGO único para sua campanha (ex: ESCOLAFREIRE25). Este código será usado pelos participantes para se juntarem à sua coleta.\nUse apenas letras e números, sem espaços.")
    return ID_CAMPANHA

async def receber_id_campanha(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe o código, valida, salva no banco e finaliza o cadastro."""
    id_campanha = update.message.text.upper()
    db = SessionLocal()
    try:
        # Verifica se o código de campanha já existe
        existente = db.query(PontoFocal).filter(PontoFocal.id_campanha == id_campanha).first()
        if existente:
            await update.message.reply_text("Este código de campanha já está em uso. Por favor, escolha outro.")
            return ID_CAMPANHA # Pede para tentar de novo

        # Se não existe, cria o novo Ponto Focal
        novo_ponto_focal = PontoFocal(
            id_campanha=id_campanha,
            nome_instituicao=context.user_data['nome_instituicao'],
            nome_responsavel=context.user_data['nome_responsavel'],
            admin_telegram_id=update.effective_user.id
        )
        db.add(novo_ponto_focal)
        db.commit()

        await update.message.reply_text(
            f"✅ Sucesso! Sua instituição '{novo_ponto_focal.nome_instituicao}' foi cadastrada.\n"
            f"Seu código de campanha é: {id_campanha}\n\n"
            "Divulgue este código para que as pessoas possam participar. Obrigado por transformar óleo em futuro!"
        )
        context.user_data.clear()
        return ConversationHandler.END
    finally:
        db.close()


# --- FLUXO DE PARTICIPAÇÃO E DOAÇÃO DO GERADOR ---

async def participar_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia o fluxo para um usuário se associar a uma campanha."""
    await update.message.reply_text("Para participar, digite o Código da Campanha da sua instituição.")
    return CODIGO_ASSOCIAR

async def receber_codigo_associar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Associa o gerador a um Ponto Focal existente."""
    codigo_campanha = update.message.text.upper()
    user = update.effective_user
    db = SessionLocal()
    try:
        ponto_focal = db.query(PontoFocal).filter(PontoFocal.id_campanha == codigo_campanha).first()
        if not ponto_focal:
            await update.message.reply_text("Código de campanha não encontrado. Verifique e tente novamente.")
            return CODIGO_ASSOCIAR

        # Cria o novo gerador
        novo_gerador = Gerador(
            telegram_id=user.id,
            nome_usuario=user.first_name,
            ponto_focal_id=ponto_focal.id
        )
        db.add(novo_gerador)
        db.commit()

        await update.message.reply_text(
            f"Parabéns! Você agora está participando da campanha da '{ponto_focal.nome_instituicao}'.\n"
            "Para registrar sua próxima entrega de óleo, use o comando /doar."
        )
        return ConversationHandler.END
    finally:
        db.close()

async def doar_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia o fluxo de registro de doação."""
    user_id = update.effective_user.id
    db = SessionLocal()
    try:
        gerador = db.query(Gerador).filter(Gerador.telegram_id == user_id).first()
        if not gerador:
            await update.message.reply_text("Você ainda não está participando de nenhuma campanha. Use /participar primeiro.")
            return ConversationHandler.END
        
        await update.message.reply_text("Legal! Quantos litros de óleo (aproximadamente) você está doando?")
        return QUANTIDADE_LITROS
    finally:
        db.close()

async def receber_quantidade_litros(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe os litros, gera o código de entrega e salva no banco."""
    try:
        litros = float(update.message.text.replace(',', '.'))
    except ValueError:
        await update.message.reply_text("Por favor, digite um número válido para os litros (ex: 2 ou 3.5).")
        return QUANTIDADE_LITROS

    user_id = update.effective_user.id
    db = SessionLocal()
    try:
        gerador = db.query(Gerador).filter(Gerador.telegram_id == user_id).first()
        # Gera um código de entrega único
        codigo_entrega = "OLEO-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        
        nova_doacao = Doacao(
            id_entrega=codigo_entrega,
            gerador_id=gerador.id,
            litros_informados=litros,
            status='pendente'
        )
        db.add(nova_doacao)
        db.commit()

        await update.message.reply_text(
            "Sua intenção de doação foi registrada com sucesso!\n\n"
            f"Ao levar o óleo ao ponto de coleta, por favor, mostre este código para o responsável:\n\n"
            f"**{codigo_entrega}**\n\n"
            "Muito obrigado por sua contribuição!"
        )
        return ConversationHandler.END
    finally:
        db.close()


# --- COMANDOS GERAIS E DE ADMIN ---

async def validar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Valida uma entrega de óleo. Apenas para Pontos Focais."""
    user_id = update.effective_user.id
    db = SessionLocal()
    try:
        ponto_focal = db.query(PontoFocal).filter(PontoFocal.admin_telegram_id == user_id).first()
        if not ponto_focal:
            await update.message.reply_text("Este comando é apenas para administradores de Pontos de Coleta.")
            return

        if not context.args:
            await update.message.reply_text("Uso incorreto. Envie o comando seguido do código. Ex: /validar OLEO-ABCD")
            return

        codigo_entrega = context.args[0].upper()
        doacao = db.query(Doacao).filter(Doacao.id_entrega == codigo_entrega).first()

        if not doacao:
            await update.message.reply_text("Código de entrega não encontrado.")
            return
        
        if doacao.status == 'validado':
            await update.message.reply_text("Esta doação já foi validada anteriormente.")
            return
        
        # Verifica se a doação pertence à campanha deste Ponto Focal
        if doacao.gerador.ponto_focal_id != ponto_focal.id:
            await update.message.reply_text("ERRO: Esta doação pertence a outra campanha e não pode ser validada aqui.")
            return

        # Valida a doação
        doacao.status = 'validado'
        ponto_focal.litros_validados += doacao.litros_informados
        db.commit()

        # Notifica o doador (se possível)
        try:
            await context.bot.send_message(
                chat_id=doacao.gerador.telegram_id,
                text=f"Boas notícias! Sua doação de {doacao.litros_informados}L foi validada na '{ponto_focal.nome_instituicao}'. Obrigado!"
            )
        except Exception as e:
            logger.error(f"Não foi possível notificar o doador {doacao.gerador.telegram_id}: {e}")

        await update.message.reply_text(
            f"✅ Doação de {doacao.litros_informados}L de {doacao.gerador.nome_usuario} validada com sucesso!\n"
            f"O total da sua campanha agora é de {ponto_focal.litros_validados:.2f} litros."
        )

    finally:
        db.close()

async def placar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra o total de litros arrecadados na campanha do usuário."""
    user_id = update.effective_user.id
    db = SessionLocal()
    try:
        gerador = db.query(Gerador).filter(Gerador.telegram_id == user_id).first()
        ponto_focal_admin = db.query(PontoFocal).filter(PontoFocal.admin_telegram_id == user_id).first()

        if not gerador and not ponto_focal_admin:
            await update.message.reply_text("Você precisa participar de uma campanha para ver o placar. Use /participar.")
            return
        
        ponto_focal = gerador.ponto_focal if gerador else ponto_focal_admin
        
        total = ponto_focal.litros_validados
        nome_campanha = ponto_focal.nome_instituicao
        
        await update.message.reply_text(
            f"📊 Placar da Campanha '{nome_campanha}' \n\n"
            f"Já arrecadamos um total de {total:.2f} litros de óleo!\n\n"
            "Continue participando para ajudarmos ainda mais!"
        )
    finally:
        db.close()


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela e encerra a conversa atual."""
    await update.message.reply_text(
        "Operação cancelada.", reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ConversationHandler.END
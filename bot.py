import logging
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters
import config
import database
import handlers

# Configura o logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Função principal que inicia o bot."""
    # Garante que o banco de dados e as tabelas sejam criados ao iniciar
    database.criar_banco()

    # Cria a aplicação do bot usando o token do arquivo de configuração
    application = Application.builder().token(config.TELEGRAM_TOKEN).build()

    # --- Conversas (Fluxos com Múltiplos Passos) ---

    # Conversa para cadastrar um novo Ponto Focal
    conv_handler_cadastro = ConversationHandler(
        entry_points=[CommandHandler("cadastrar_local", handlers.cadastrar_local_start)],
        states={
            handlers.NOME_INSTITUICAO: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.receber_nome_instituicao)],
            handlers.NOME_RESPONSAVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.receber_nome_responsavel)],
            handlers.ID_CAMPANHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.receber_id_campanha)],
        },
        fallbacks=[CommandHandler("cancelar", handlers.cancelar)],
    )

    # Conversa para um Gerador se associar a uma campanha
    conv_handler_participar = ConversationHandler(
        entry_points=[CommandHandler("participar", handlers.participar_start)],
        states={
            handlers.CODIGO_ASSOCIAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.receber_codigo_associar)],
        },
        fallbacks=[CommandHandler("cancelar", handlers.cancelar)],
    )

    # Conversa para registrar uma doação
    conv_handler_doar = ConversationHandler(
        entry_points=[CommandHandler("doar", handlers.doar_start)],
        states={
            handlers.QUANTIDADE_LITROS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.receber_quantidade_litros)],
        },
        fallbacks=[CommandHandler("cancelar", handlers.cancelar)],
    )
    
    # Adiciona as conversas ao bot
    application.add_handler(conv_handler_cadastro)
    application.add_handler(conv_handler_participar)
    application.add_handler(conv_handler_doar)

    # --- Comandos Simples ---
    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CommandHandler("help", handlers.start)) # Alias para /start
    application.add_handler(CommandHandler("validar", handlers.validar))
    application.add_handler(CommandHandler("placar", handlers.placar))
    application.add_handler(CommandHandler("cancelar", handlers.cancelar))

    # Inicia o bot
    logger.info("Iniciando o bot...")
    application.run_polling()

if __name__ == "__main__":
    main()
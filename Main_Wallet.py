import streamlit as st
from web3 import Web3
from stellar_sdk import Server, Keypair, TransactionBuilder, Network, Asset
import requests
import json
import os
from dotenv import load_dotenv
from streamlit.components.v1 import html

# Configurações iniciais
load_dotenv()
INFURA_URL = f"https://goerli.infura.io/v3/{os.getenv('INFURA_API_KEY')}"
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')
HORIZON_URL = "https://horizon-testnet.stellar.org"
NETWORK_PASSPHRASE = Network.TESTNET_NETWORK_PASSPHRASE

# Inicializar conexões
w3 = Web3(Web3.HTTPProvider(INFURA_URL))
server = Server(HORIZON_URL)

# ABI ERC20 (simplificado)
ERC20_ABI = json.loads('''[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf",
"outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":false,"inputs":[{"name":"_to","type":"address"},
{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"type":"function"}]''')

# Componentes personalizados
def meta_mask_connector():
    html('''
    <script src="https://cdn.jsdelivr.net/npm/web3@1.5.2/dist/web3.min.js"></script>
    <script>
    async function connectMetaMask() {
        if (window.ethereum) {
            try {
                await window.ethereum.enable();
                const web3 = new Web3(window.ethereum);
                const accounts = await web3.eth.getAccounts();
                window.parent.postMessage({
                    type: 'METAMASK_ACCOUNTS',
                    accounts: accounts
                }, '*');
            } catch (error) {
                console.error(error);
            }
        }
    }
    </script>
    <button onclick="connectMetaMask()" style="padding: 10px; background: #f6851b; color: white; border: none; border-radius: 5px;">
        Conectar MetaMask
    </button>
    ''')

def main():
    st.title("🪙 Multi-Blockchain Wallet DApp")
    
    menu = st.sidebar.selectbox("Blockchain", ["Ethereum", "Stellar"])
    
    if menu == "Ethereum":
        handle_ethereum()
    else:
        handle_stellar()

# ... (As funções handle_ethereum e handle_stellar serão expandidas abaixo)

def handle_ethereum():
    st.header("💰 Carteira Ethereum")
    
    with st.expander("🔗 Conectar MetaMask"):
        meta_mask_connector()
    
    tab1, tab2, tab3, tab4 = st.tabs(["🧩 Carteira", "💸 Transferir", "🪙 Tokens", "📜 Histórico"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✨ Nova Carteira"):
                account = w3.eth.account.create()
                st.success("Carteira Gerada!")
                st.code(f"Endereço: {account.address}")
                st.code(f"Chave Privada: {account.key.hex()}")
        
        with col2:
            with st.form("eth_balance_form"):
                address = st.text_input("Endereço Ethereum")
                if st.form_submit_button("📊 Ver Saldo"):
                    try:
                        balance = w3.eth.get_balance(address)
                        st.success(f"Saldo: {w3.from_wei(balance, 'ether'):.4f} ETH")
                    except:
                        st.error("Endereço inválido")
    
    with tab2:
        with st.form("eth_transfer_form"):
            col1, col2 = st.columns(2)
            with col1:
                private_key = st.text_input("Chave Privada", type="password")
            with col2:
                recipient = st.text_input("Destinatário")
            
            amount = st.number_input("Quantidade (ETH)", min_value=0.001, step=0.001)
            
            if st.form_submit_button("🚀 Enviar Transação"):
                try:
                    account = w3.eth.account.from_key(private_key)
                    nonce = w3.eth.get_transaction_count(account.address)
                    tx = {
                        'nonce': nonce,
                        'to': recipient,
                        'value': w3.to_wei(amount, 'ether'),
                        'gas': 21000,
                        'gasPrice': w3.eth.gas_price
                    }
                    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
                    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                    st.success(f"Transação enviada! [Ver no Explorer](https://goerli.etherscan.io/tx/{tx_hash.hex()})")
                except Exception as e:
                    st.error(f"Erro: {str(e)}")
    
    with tab3:
        with st.form("erc20_form"):
            contract_address = st.text_input("Contrato ERC20")
            wallet_address = st.text_input("Endereço da Carteira")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("📊 Ver Saldo"):
                    try:
                        contract = w3.eth.contract(address=contract_address, abi=ERC20_ABI)
                        balance = contract.functions.balanceOf(wallet_address).call()
                        st.success(f"Saldo: {balance / 10**18:.2f} tokens")
                    except:
                        st.error("Contrato inválido")
            
            with col2:
                recipient = st.text_input("Destinatário Token")
                amount = st.number_input("Quantidade", min_value=0.1)
                
                if st.form_submit_button("🔄 Transferir"):
                    try:
                        contract = w3.eth.contract(address=contract_address, abi=ERC20_ABI)
                        tx = contract.functions.transfer(
                            recipient,
                            int(amount * 10**18)
                        ).buildTransaction({
                            'chainId': 5,  # Goerli
                            'gas': 100000,
                            'gasPrice': w3.eth.gas_price,
                            'nonce': w3.eth.get_transaction_count(wallet_address),
                        })
                        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
                        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                        st.success(f"Transação enviada! [Ver no Explorer](https://goerli.etherscan.io/tx/{tx_hash.hex()})")
                    except Exception as e:
                        st.error(f"Erro: {str(e)}")
    
    with tab4:
        address = st.text_input("Endereço para histórico")
        if st.button("🔍 Buscar Transações"):
            try:
                url = f"https://api-goerli.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=asc&apikey={ETHERSCAN_API_KEY}"
                response = requests.get(url)
                transactions = response.json()['result']
                
                for tx in transactions[:5]:
                    st.write(f"📄 {tx['hash']} | Valor: {int(tx['value']) / 10**18} ETH")
            except:
                st.error("Erro ao buscar transações")

def handle_stellar():
    st.header("🌠 Carteira Stellar")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🧩 Carteira", "💸 Transferir", "🔐 Multi-Sig", "📜 Histórico"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✨ Nova Carteira Stellar"):
                keypair = Keypair.random()
                st.success("Carteira Gerada!")
                st.code(f"Pública: {keypair.public_key}")
                st.code(f"Secreta: {keypair.secret}")
        
        with col2:
            with st.form("stellar_balance_form"):
                public_key = st.text_input("Chave Pública")
                if st.form_submit_button("📊 Ver Saldo"):
                    try:
                        account = server.accounts().account_id(public_key).call()
                        balances = account['balances']
                        for balance in balances:
                            st.write(f"💰 {balance['balance']} {balance['asset_type']}")
                    except:
                        st.error("Conta inválida")
    
    with tab2:
        with st.form("stellar_transfer_form"):
            col1, col2 = st.columns(2)
            with col1:
                secret_key = st.text_input("Chave Secreta", type="password")
            with col2:
                destination = st.text_input("Destinatário")
            
            amount = st.number_input("Quantidade (XLM)", min_value=1.0)
            asset_code = st.selectbox("Ativo", ["XLM", "Personalizado"])
            
            if asset_code == "Personalizado":
                custom_asset = st.text_input("Código do Ativo")
                asset_issuer = st.text_input("Emissor do Ativo")
                asset = Asset(custom_asset, asset_issuer)
            else:
                asset = Asset.native()
            
            if st.form_submit_button("🚀 Enviar Transação"):
                try:
                    source_keypair = Keypair.from_secret(secret_key)
                    source_account = server.load_account(source_keypair.public_key)
                    
                    transaction = (
                        TransactionBuilder(
                            source_account=source_account,
                            network_passphrase=NETWORK_PASSPHRASE,
                            base_fee=100
                        )
                        .append_payment_op(
                            destination=destination,
                            amount=str(amount),
                            asset=asset
                        )
                        .build()
                    )
                    
                    transaction.sign(source_keypair)
                    response = server.submit_transaction(transaction)
                    st.success(f"Transação bem sucedida! [Ver no Explorer](https://stellar.expert/explorer/testnet/tx/{response['hash']})")
                except Exception as e:
                    st.error(f"Erro: {str(e)}")
    
    with tab3:
        with st.form("multisig_form"):
            secret_key = st.text_input("Chave Secreta Principal", type="password")
            signer_key = st.text_input("Chave do Signatário Adicional")
            threshold = st.number_input("Limiar de Assinaturas", min_value=1, max_value=3, value=2)
            
            if st.form_submit_button("🔏 Configurar Multi-Sig"):
                try:
                    source_keypair = Keypair.from_secret(secret_key)
                    source_account = server.load_account(source_keypair.public_key)
                    
                    transaction = (
                        TransactionBuilder(
                            source_account=source_account,
                            network_passphrase=NETWORK_PASSPHRASE,
                            base_fee=100
                        )
                        .append_set_options_op(
                            signer={
                                'ed25519_public_key': signer_key,
                                'weight': 1
                            },
                            master_weight=1,
                            low_threshold=threshold,
                            med_threshold=threshold,
                            high_threshold=threshold
                        )
                        .build()
                    )
                    
                    transaction.sign(source_keypair)
                    response = server.submit_transaction(transaction)
                    st.success("Configuração Multi-Sig atualizada!")
                except Exception as e:
                    st.error(f"Erro: {str(e)}")
    
    with tab4:
        address = st.text_input("Endereço para histórico")
        if st.button("🔍 Buscar Transações"):
            try:
                transactions = server.transactions().for_account(address).call()["_embedded"]["records"]
                
                for tx in transactions[:5]:
                    st.write(f"📄 {tx['hash']} | Criado em: {tx['created_at']}")
            except:
                st.error("Erro ao buscar transações")

if __name__ == "__main__":
    main()

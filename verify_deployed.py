import os, json
from web3 import Web3

which_chain = 'mainnet'

if which_chain == 'testnet':
    RPC_URL = "https://rpc-devnet-cardano-evm.c1.milkomeda.com"
    FACTORY_ADDR = "0x57A8C24B2B0707478f91D3233A264eD77149D408"
    ROUTER_ADDR = "0x5e86ED2DB18ae2cECF6989612DEB59917b897e5d"
    WETH_ADDR = "0x65a51E52eCD17B641f8F0D1d56a6c9738951FDC9"
    DEPLOYER_ADDR = "0xA4A8383e56868499EF7882167F887C30d2E20196"
    MILK_ADDR = "0x2D7289Df2f41a25D3A628258081aD7B99eb4C83B"
    SPOON_ADDR = "0xc7f4d2d2A9c3BCDbC5570d98BB10a02773Fd0340"

    FACTORY_TX = '0x9596f219eb07ffef81380baa34d410558948060dbf5dbc2edd0871063c7da29f'
    ROUTER_TX = '0x6dfb4d7a27bc15e8f0f5cb04216a84fe34aa27159fa42f860a9c39365f94a239'
    FARMING_TX = '0x0094a106af38601671ca888311542e889bc4923f7c695725775d21ac3709ce42'
    FARMING_BLOCK = 3037679

    # Note: testnet deployed contract differences:
    # - MuesliPair.sol:     fees are 0.20% (0.03%)
    # - MuesliFactory.sol:  init pair hash will probably differ
    # - MuesliRouter.sol:   same, change init pair hash to:
    #       14086ce528ba8c8c1f854ecdaf709b0434e84b44409875ce9294d60caf9270a1
    # - MasterChef.sol:     deploy block is 3037679

elif which_chain == 'mainnet':
    RPC_URL = "https://rpc-mainnet-cardano-evm.c1.milkomeda.com"
    WETH_ADDR = "0xAE83571000aF4499798d1e3b0fA0070EB3A3E3F9"
    FACTORY_ADDR = "0x57A8C24B2B0707478f91D3233A264eD77149D408"
    ROUTER_ADDR = "0x1662EBa5ff3546D407ee0c73d94665d96dad2C2A"
    DEPLOYER_ADDR = "0xA4A8383e56868499EF7882167F887C30d2E20196"
    MILK_ADDR = "0x2D7289Df2f41a25D3A628258081aD7B99eb4C83B"
    SPOON_ADDR = "0xc7f4d2d2A9c3BCDbC5570d98BB10a02773Fd0340"

    FACTORY_TX = "0x05d56c55eda37a093b309d8a4d4957ab360b5031555446081189a278b3d4f146"
    ROUTER_TX = "0x884b52b72cef277f5a250b53199f846a6dfdcc00930adb986f0e76362ec3b66d"
    FARMING_TX = "0xe9c939e44b78d82be64fc37f0c739aecb5eb4da7b88897eab58abc301cf8d9ec"
    FARMING_BLOCK = 2041728

else:
    raise Exception("Unknown chain")


provider = Web3.HTTPProvider(RPC_URL)
w3 = Web3(provider)
if not w3.isConnected():
    print(f"Error: Couldn't connect to {RPC_URL}")
    exit(1)

def compare_contract(w3, deploy_tx_hash, filename, name, args):
    deploy_tx = w3.eth.get_transaction(deploy_tx_hash)
    deploy_tx_code = deploy_tx['input']
    # deployed_code = binascii.hexlify(w3.eth.get_code(address)).decode('utf8')
    if not os.path.exists(filename):
        print(f"Error: file {filename} not found. Did you clone the repo and run yarn compile?")
        exit(1)
    with open(filename) as f:
        obj = json.load(f)
        try:
            compiled_code = obj['evm']['bytecode']['object']
        except:
            compiled_code = obj['bytecode']
        abi = obj['abi']
        contract = w3.eth.contract(abi=abi, bytecode=compiled_code)
        test_code = contract.constructor(*args).buildTransaction()['data']
    #print("Lengths: %d %d" % (len(test_code), len(deploy_tx_code)))
    
    # Metadata (last 32 bytes) differs by development environment and isn't comparable
    # See: https://ethereum.stackexchange.com/questions/94115/cannot-verify-contract-bytecode-has-small-difference
    solc_idx = test_code.find('736f6c63')
    metadata_idx = solc_idx - 64 - 2
    test_code = test_code[:metadata_idx] + test_code[solc_idx:]
    deploy_tx_code = deploy_tx_code[:metadata_idx] + deploy_tx_code[solc_idx:]

    if test_code == deploy_tx_code:
        print(f"[OK] Contract '{name}' deployed in tx {deploy_tx_hash} matches with {filename}")
        return True
    else:
        print(f"[ERR] Contract '{name}' deployed in tx {deploy_tx_hash} doesn't match with {filename} !")
        return False


if __name__ == "__main__":
    compare_contract(w3, FACTORY_TX, "muesli-core/build/MuesliFactory.json", "factory", [DEPLOYER_ADDR])
    compare_contract(w3, ROUTER_TX, "muesli-periphery/build/MuesliRouter.json", "router", 
        [FACTORY_ADDR, WETH_ADDR]  # constructor
    )
    compare_contract(w3, FARMING_TX, "muesli-farming/build/contracts/MasterChef.json", "farmer", 
        [MILK_ADDR, SPOON_ADDR, DEPLOYER_ADDR, 1, FARMING_BLOCK]  # constructor
    )

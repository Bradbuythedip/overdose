import React, { useMemo } from 'react'
import styled from 'styled-components'
import { motion } from 'framer-motion'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ConnectionProvider, WalletProvider } from '@solana/wallet-adapter-react'
import { WalletAdapterNetwork } from '@solana/wallet-adapter-base'
import { PhantomWalletAdapter } from '@solana/wallet-adapter-phantom'
import { WalletModalProvider } from '@solana/wallet-adapter-react-ui'
import { clusterApiUrl } from '@solana/web3.js'

// Components imports
import Hero from './components/Hero'
import About from './components/About'
import Article from './components/Article'
import Puzzle from './components/Puzzle'
import Resources from './components/Resources'
import CTA from './components/CTA'
import Footer from './components/Footer'
import HuntContent from './components/HuntContent'

const AppContainer = styled.div`
  background-color: #0a0a0f;
  color: #ffffff;
  min-height: 100vh;
`

const HomePage = () => (
  <>
    <Hero />
    <About />
    <Article />
    <Puzzle />
    <Resources />
    <CTA />
    <Footer />
  </>
)

const App = () => {
  // You can change this to 'mainnet-beta' for production
  const network = WalletAdapterNetwork.Devnet
  const endpoint = useMemo(() => clusterApiUrl(network), [network])
  
  const wallets = useMemo(
    () => [
      new PhantomWalletAdapter(),
    ],
    []
  )

  return (
    <ConnectionProvider endpoint={endpoint}>
      <WalletProvider wallets={wallets} autoConnect>
        <WalletModalProvider>
          <Router>
            <AppContainer>
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/hunt" element={<HuntContent />} />
              </Routes>
            </AppContainer>
          </Router>
        </WalletModalProvider>
      </WalletProvider>
    </ConnectionProvider>
  )
}

export default App
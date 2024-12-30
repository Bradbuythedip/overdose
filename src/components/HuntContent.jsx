import React, { useState, useEffect } from 'react'
import styled from 'styled-components'
import { motion } from 'framer-motion'
import { FaLock, FaArrowRight, FaArrowLeft } from 'react-icons/fa'
import { useConnection, useWallet } from '@solana/wallet-adapter-react'
import { WalletMultiButton } from '@solana/wallet-adapter-react-ui'
import { LAMPORTS_PER_SOL, Transaction, SystemProgram } from '@solana/web3.js'
import { PublicKey } from '@solana/web3.js'

// Import wallet adapter CSS
import '@solana/wallet-adapter-react-ui/styles.css'

const HuntSection = styled.section`
  min-height: 100vh;
  background: #0a0a0f;
  padding: 5rem 2rem;
`

const Container = styled.div`
  max-width: 1200px;
  margin: 0 auto;
`

const PaywallContainer = styled(motion.div)`
  background: rgba(18, 18, 26, 0.95);
  padding: 3rem;
  border-radius: 15px;
  text-align: center;
  box-shadow: 0 0 30px rgba(0, 242, 255, 0.1);
`

const ContentContainer = styled(motion.div)`
  background: rgba(18, 18, 26, 0.95);
  padding: 3rem;
  border-radius: 15px;
  margin-top: 2rem;
`

const Title = styled.h2`
  font-size: 2.5rem;
  color: #00f2ff;
  margin-bottom: 2rem;
`

const WalletButton = styled(WalletMultiButton)`
  background-color: #00f2ff !important;
  color: #0a0a0f !important;
  border: none !important;
  border-radius: 8px !important;
  padding: 1rem 2rem !important;
  font-size: 1.2rem !important;
  cursor: pointer !important;
  transition: all 0.3s ease !important;
  margin: 1rem auto !important;
  display: block !important;

  &:hover {
    opacity: 0.9 !important;
    transform: scale(1.05) !important;
  }

  &:active {
    transform: scale(0.95) !important;
  }
`

const Price = styled.div`
  font-size: 2rem;
  color: #ffffff;
  margin: 2rem 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
`

const PriceAmount = styled.span`
  color: #00f2ff;
`

const PayButton = styled(motion.button)`
  padding: 1rem 2rem;
  font-size: 1.2rem;
  background: #00f2ff;
  border: none;
  color: #0a0a0f;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 1rem auto;
  transition: all 0.3s ease;

  &:hover {
    opacity: 0.9;
    transform: scale(1.05);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`

const PageNavigation = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 2rem;
`

const NavButton = styled(motion.button)`
  padding: 0.8rem 1.5rem;
  font-size: 1rem;
  background: transparent;
  border: 1px solid #00f2ff;
  color: #00f2ff;
  border-radius: 5px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  &:hover:not(:disabled) {
    background: #00f2ff;
    color: #0a0a0f;
  }
`

const PageIndicator = styled.div`
  color: #ffffff;
  font-size: 1.2rem;
`

const ContentPage = styled.div`
  color: #ffffff;
  line-height: 1.8;
  font-size: 1.1rem;

  img {
    max-width: 100%;
    border-radius: 8px;
    margin: 2rem 0;
  }
`

const Description = styled.p`
  color: #888;
  margin-bottom: 2rem;
  line-height: 1.6;
`

const PAYMENT_AMOUNT = 0.01 * LAMPORTS_PER_SOL // 0.01 SOL
const RECEIVER_WALLET = new PublicKey('7JU6pUxPXtqdvE9XpK4hRADBwoC9s1FhdLauUnLxLDti')

const HuntContent = () => {
  const [hasAccess, setHasAccess] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [isLoading, setIsLoading] = useState(false)
  const totalPages = 7 // Total number of content pages

  const { connection } = useConnection()
  const { publicKey, sendTransaction } = useWallet()

  // Check if user has already paid (could be expanded to check on-chain)
  useEffect(() => {
    const checkAccess = async () => {
      if (publicKey) {
        // Here you would typically check if the user's wallet has already paid
        // For now, we'll just check localStorage
        const hasStoredAccess = localStorage.getItem(`huntAccess_${publicKey.toString()}`)
        if (hasStoredAccess) {
          setHasAccess(true)
        }
      }
    }
    checkAccess()
  }, [publicKey])

  const handlePayment = async () => {
    if (!publicKey) return

    try {
      setIsLoading(true)

      const transaction = new Transaction().add(
        SystemProgram.transfer({
          fromPubkey: publicKey,
          toPubkey: RECEIVER_WALLET,
          lamports: PAYMENT_AMOUNT,
        })
      )

      const signature = await sendTransaction(transaction, connection)
      await connection.confirmTransaction(signature, 'confirmed')

      // Store access in localStorage
      localStorage.setItem(`huntAccess_${publicKey.toString()}`, 'true')
      setHasAccess(true)
    } catch (error) {
      console.error('Payment failed:', error)
      alert('Payment failed. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handlePreviousPage = () => {
    if (currentPage > 1) {
      setCurrentPage(prev => prev - 1)
    }
  }

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(prev => prev + 1)
    }
  }

  // Content for each page
  const pageContent = {
    1: {
      title: "The Beginning of the Hunt",
      content: "In the depths of Max Keiser's article lies a secret that could change your life forever. As you begin this journey, remember that the key isn't just in the words - it's in the patterns, the spaces, and perhaps even in plain sight...",
      image: "/images/IMG_6244.jpeg"
    },
    2: {
      title: "Decoding the First Clue",
      content: "The first step in finding the hidden 20 BTC requires understanding the fundamental structure of Bitcoin private keys. Look closely at the formatting and spacing of certain paragraphs...",
      image: "/images/IMG_6245.jpeg"
    },
    // Add more pages as needed
  }

  if (!hasAccess) {
    return (
      <HuntSection>
        <Container>
          <PaywallContainer
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <FaLock size={40} color="#00f2ff" />
            <Title>Access the Hunt</Title>
            <Description>
              Get exclusive access to detailed analysis, clues, and progress tracking in the hunt for Max Keiser's hidden 20 BTC.
            </Description>
            <Price>
              <img src="/solana-logo.png" alt="SOL" style={{ width: '24px', height: '24px' }} />
              <PriceAmount>0.1 SOL</PriceAmount>
            </Price>
            <WalletButton />
            {publicKey && (
              <PayButton
                onClick={handlePayment}
                disabled={isLoading}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                {isLoading ? 'Processing...' : 'Pay 0.1 SOL for Access'}
              </PayButton>
            )}
          </PaywallContainer>
        </Container>
      </HuntSection>
    )
  }

  return (
    <HuntSection>
      <Container>
        <ContentContainer
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <Title>{pageContent[currentPage]?.title || `Chapter ${currentPage}`}</Title>
          <ContentPage>
            {pageContent[currentPage]?.image && (
              <img src={pageContent[currentPage].image} alt={`Hunt content page ${currentPage}`} />
            )}
            {pageContent[currentPage]?.content || "Content coming soon..."}
          </ContentPage>
          <PageNavigation>
            <NavButton 
              onClick={handlePreviousPage}
              disabled={currentPage === 1}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <FaArrowLeft /> Previous
            </NavButton>
            <PageIndicator>
              Page {currentPage} of {totalPages}
            </PageIndicator>
            <NavButton 
              onClick={handleNextPage}
              disabled={currentPage === totalPages}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Next <FaArrowRight />
            </NavButton>
          </PageNavigation>
        </ContentContainer>
      </Container>
    </HuntSection>
  )
}

export default HuntContent
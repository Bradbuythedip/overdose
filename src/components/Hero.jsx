import React from 'react'
import { useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import { motion } from 'framer-motion'

const HeroSection = styled.section`
  height: 100vh;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  background: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)),
              url('/images/IMG_6244.jpeg');
  background-size: cover;
  background-position: center;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(45deg, rgba(0, 242, 255, 0.1), rgba(255, 0, 128, 0.1));
    animation: gradientAnimation 15s ease infinite;
  }
`

const HeroContent = styled(motion.div)`
  position: relative;
  z-index: 1;
`

const Title = styled(motion.h1)`
  font-size: 4rem;
  margin-bottom: 1rem;
  color: #ffffff;
  text-shadow: 0 0 20px rgba(0, 242, 255, 0.5);

  @media (max-width: 768px) {
    font-size: 2.5rem;
  }
`

const Subtitle = styled(motion.h2)`
  font-size: 2rem;
  margin-bottom: 2rem;
  color: #00f2ff;

  @media (max-width: 768px) {
    font-size: 1.5rem;
  }
`

const CTAButton = styled(motion.button)`
  padding: 1rem 2rem;
  font-size: 1.2rem;
  background: transparent;
  border: 2px solid #00f2ff;
  color: #00f2ff;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    background: #00f2ff;
    color: #0a0a0f;
  }
`

const Hero = () => {
  const navigate = useNavigate()
  return (
    <HeroSection>
      <HeroContent
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1 }}
      >
        <Title
          animate={{ 
            textShadow: [
              "0 0 20px rgba(0, 242, 255, 0.5)",
              "0 0 40px rgba(0, 242, 255, 0.7)",
              "0 0 20px rgba(0, 242, 255, 0.5)"
            ]
          }}
          transition={{ 
            duration: 2,
            repeat: Infinity
          }}
        >
          OVERDOSE
        </Title>
        <Subtitle>Featuring Max Keiser's Hidden 20 BTC</Subtitle>
        <CTAButton
          onClick={() => navigate('/hunt')}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          Start the Hunt
        </CTAButton>
      </HeroContent>
    </HeroSection>
  )
}

export default Hero
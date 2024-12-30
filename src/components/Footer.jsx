import React from 'react'
import styled from 'styled-components'
import { motion } from 'framer-motion'
import { FaTelegram, FaDiscord } from 'react-icons/fa'
import { UilTwitterAlt } from '@iconscout/react-unicons'

const FooterSection = styled.footer`
  padding: 3rem 2rem;
  background-color: #0a0a0f;
  border-top: 1px solid #2a2a3a;
`

const Container = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
`

const FooterColumn = styled.div`
  text-align: center;
`

const Title = styled.h3`
  color: #00f2ff;
  margin-bottom: 1rem;
  font-size: 1.5rem;
`

const Description = styled.p`
  color: #ffffff;
  margin-bottom: 1rem;
`

const SocialLinks = styled.div`
  display: flex;
  justify-content: center;
  gap: 1rem;
`

const SocialLink = styled(motion.a)`
  color: #ffffff;
  font-size: 1.5rem;
  transition: color 0.3s ease;

  &:hover {
    color: #00f2ff;
  }
`

const Copyright = styled.div`
  text-align: center;
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid #2a2a3a;
  color: #888;
`

const Footer = () => {
  return (
    <FooterSection>
      <Container>
        <FooterColumn>
          <Title>$OVERDOSE</Title>
          <Description>The memecoin that's hiding 20 BTC</Description>
          <Description style={{ fontSize: '0.8rem', marginTop: '1rem', color: '#00f2ff' }}>
            Contract: <a href="https://solscan.io/address/2722Zpk2jDLFjKdqeFe1GBgYxN1SLR3ioVNiojrppump" target="_blank" rel="noopener noreferrer" style={{ color: '#00f2ff', textDecoration: 'underline' }}>2722Zpk2jDLFjKdqeFe1GBgYxN1SLR3ioVNiojrppump</a>
          </Description>
        </FooterColumn>
        
        <FooterColumn>
          <Title>Follow Us</Title>
          <SocialLinks>
            <SocialLink 
              href="https://x.com/notMaxKeiser" 
              target="_blank"
              rel="noopener noreferrer"
              whileHover={{ scale: 1.2 }}
              whileTap={{ scale: 0.9 }}
            >
              <UilTwitterAlt style={{ transform: 'scale(1.2)' }} />
            </SocialLink>
            <SocialLink 
              href="#" 
              target="_blank"
              rel="noopener noreferrer"
              whileHover={{ scale: 1.2 }}
              whileTap={{ scale: 0.9 }}
            >
              <FaTelegram />
            </SocialLink>
            <SocialLink 
              href="#" 
              target="_blank"
              rel="noopener noreferrer"
              whileHover={{ scale: 1.2 }}
              whileTap={{ scale: 0.9 }}
            >
              <FaDiscord />
            </SocialLink>
          </SocialLinks>
        </FooterColumn>

        <FooterColumn>
          <Title>Legal</Title>
          <Description>
            © 2024 $OVERDOSE. All rights reserved.
          </Description>
        </FooterColumn>
      </Container>
      <Copyright>
        Designed and developed with 💙 for the crypto community
      </Copyright>
    </FooterSection>
  )
}

export default Footer
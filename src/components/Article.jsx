import React from 'react'
import styled from 'styled-components'
import { motion } from 'framer-motion'

const ArticleSection = styled.section`
  padding: 5rem 2rem;
  background: linear-gradient(rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.8)),
              url('/images/IMG_6245.jpeg');
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
`

const Container = styled.div`
  max-width: 1200px;
  margin: 0 auto;
`

const Title = styled(motion.h2)`
  font-size: 2.5rem;
  color: #00f2ff;
  margin-bottom: 2rem;
  text-align: center;
`

const Quote = styled(motion.blockquote)`
  border-left: 4px solid #00f2ff;
  padding: 1rem 2rem;
  margin: 2rem 0;
  font-size: 1.2rem;
  background: rgba(0, 242, 255, 0.05);
  backdrop-filter: blur(10px);
`

const Author = styled.cite`
  display: block;
  margin-top: 1rem;
  color: #00f2ff;
  font-style: normal;
`

const ArticleText = styled(motion.p)`
  font-size: 1.1rem;
  line-height: 1.8;
  margin: 2rem 0;
  color: #ffffff;
`

const Article = () => {
  return (
    <ArticleSection>
      <Container>
        <Title
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
        >
          Max Keiser's 'Overdose'
        </Title>
        <Quote
          initial={{ opacity: 0, x: -20 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          <a href="https://x.com/BitcoinMagazine" target="_blank" rel="noopener noreferrer" style={{ color: '#00f2ff', textDecoration: 'none' }}>
            I hid a private #Bitcoin key encoded in this piece I wrote for @BitcoinMagazine Mr. President. Nobody's figured it out yet, but it's for 20 BTC.
          </a>
          <Author>- Max Keiser</Author>
        </Quote>
        <ArticleText
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.4 }}
        >
          A groundbreaking piece that challenges conventional financial wisdom while concealing a digital treasure worth 20 BTC. The article weaves together intricate narratives of monetary policy, technological revolution, and hidden cryptographic puzzles. Can you uncover the secret within its pages?
        </ArticleText>
      </Container>
    </ArticleSection>
  )
}

export default Article
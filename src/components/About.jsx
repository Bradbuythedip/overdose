import React from 'react'
import styled from 'styled-components'
import { motion } from 'framer-motion'

const AboutSection = styled.section`
  padding: 5rem 2rem;
  background-color: #12121a;
`

const Container = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  text-align: center;
`

const Title = styled(motion.h2)`
  font-size: 2.5rem;
  color: #00f2ff;
  margin-bottom: 2rem;
`

const Description = styled(motion.p)`
  font-size: 1.2rem;
  line-height: 1.6;
  max-width: 800px;
  margin: 0 auto;
  color: #ffffff;
`

const About = () => {
  return (
    <AboutSection>
      <Container>
        <Title
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
        >
          About OVERDOSE
        </Title>
        <Description
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          $OVERDOSE is the ultimate memecoin fusion of crypto culture and financial rebellion. Born from Max Keiser's legendary hidden Bitcoin treasure, we're not just another token - we're a movement. With 20 BTC still waiting to be discovered in Max's original piece, every holder becomes part of the greatest treasure hunt in crypto history. Are you ready to find the key?
        </Description>
      </Container>
    </AboutSection>
  )
}

export default About
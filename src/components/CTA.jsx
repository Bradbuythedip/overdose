import React from 'react'
import styled from 'styled-components'
import { motion } from 'framer-motion'

const CTASection = styled.section`
  padding: 5rem 2rem;
  background: linear-gradient(rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.8)),
              url('/images/IMG_6246.jpeg');
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
`

const Container = styled.div`
  max-width: 800px;
  margin: 0 auto;
  text-align: center;
`

const Title = styled(motion.h2)`
  font-size: 2.5rem;
  color: #00f2ff;
  margin-bottom: 1.5rem;
`

const Description = styled(motion.p)`
  font-size: 1.2rem;
  color: #ffffff;
  margin-bottom: 2rem;
`

const Form = styled(motion.form)`
  display: flex;
  gap: 1rem;
  max-width: 500px;
  margin: 0 auto;

  @media (max-width: 768px) {
    flex-direction: column;
  }
`

const Input = styled.input`
  flex: 1;
  padding: 1rem;
  border: none;
  border-radius: 5px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  font-size: 1rem;

  &::placeholder {
    color: rgba(255, 255, 255, 0.5);
  }
`

const SubmitButton = styled(motion.button)`
  padding: 1rem 2rem;
  border: none;
  border-radius: 5px;
  background: #00f2ff;
  color: #0a0a0f;
  font-size: 1rem;
  cursor: pointer;
  white-space: nowrap;
`

const CTA = () => {
  const handleSubmit = (e) => {
    e.preventDefault()
    // Handle subscription logic here
  }

  return (
    <CTASection>
      <Container>
        <Title
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
        >
          Join the Hunt
        </Title>
        <Description
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          Join the $OVERDOSE community for exclusive clues and updates
        </Description>
        <Form
          onSubmit={handleSubmit}
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.4 }}
        >
          <Input 
            type="email" 
            placeholder="Enter your email"
            required
          />
          <SubmitButton
            type="submit"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Subscribe
          </SubmitButton>
        </Form>
      </Container>
    </CTASection>
  )
}

export default CTA
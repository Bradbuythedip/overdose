import React, { useState } from 'react'
import styled from 'styled-components'
import { motion } from 'framer-motion'

const PuzzleSection = styled.section`
  padding: 5rem 2rem;
  background-color: #0a0a0f;
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

const PuzzleContainer = styled(motion.div)`
  background: rgba(18, 18, 26, 0.9);
  padding: 2rem;
  border-radius: 10px;
  box-shadow: 0 0 20px rgba(0, 242, 255, 0.2);
`

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 2rem;
  margin-bottom: 2rem;
`

const StatBox = styled(motion.div)`
  padding: 1.5rem;
  background: rgba(0, 242, 255, 0.05);
  border-radius: 8px;
`

const StatNumber = styled.span`
  display: block;
  font-size: 2.5rem;
  color: #00f2ff;
  margin-bottom: 0.5rem;
`

const StatLabel = styled.span`
  color: #ffffff;
  font-size: 1.1rem;
`

const HintBox = styled(motion.div)`
  margin-top: 3rem;
  padding: 2rem;
  border-top: 1px solid rgba(0, 242, 255, 0.2);
`

const HintButton = styled(motion.button)`
  padding: 1rem 2rem;
  font-size: 1.1rem;
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

const Puzzle = () => {
  const [currentHint, setCurrentHint] = useState(0)
  const hints = [
    "Look closely at the patterns...",
    "Some things are hidden in plain sight...",
    "The key might not be where you expect it..."
  ]

  return (
    <PuzzleSection>
      <Container>
        <Title
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
        >
          Find the Hidden Key
        </Title>
        <PuzzleContainer
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
        >
          <StatsGrid>
            <StatBox
              whileHover={{ scale: 1.05 }}
              transition={{ type: "spring", stiffness: 300 }}
            >
              <StatNumber>1,337</StatNumber>
              <StatLabel>Treasure Hunters</StatLabel>
            </StatBox>
            <StatBox
              whileHover={{ scale: 1.05 }}
              transition={{ type: "spring", stiffness: 300 }}
            >
              <StatNumber>0</StatNumber>
              <StatLabel>Keys Found</StatLabel>
            </StatBox>
            <StatBox
              whileHover={{ scale: 1.05 }}
              transition={{ type: "spring", stiffness: 300 }}
            >
              <StatNumber>20</StatNumber>
              <StatLabel>BTC Reward</StatLabel>
            </StatBox>
          </StatsGrid>
          <HintBox>
            <HintButton
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setCurrentHint((prev) => (prev + 1) % hints.length)}
            >
              {hints[currentHint]}
            </HintButton>
          </HintBox>
        </PuzzleContainer>
      </Container>
    </PuzzleSection>
  )
}

export default Puzzle
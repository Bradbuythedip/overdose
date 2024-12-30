import React from 'react'
import styled from 'styled-components'
import { motion } from 'framer-motion'

// Components imports
import Hero from './components/Hero'
import About from './components/About'
import Article from './components/Article'
import Puzzle from './components/Puzzle'
import Resources from './components/Resources'
import CTA from './components/CTA'
import Footer from './components/Footer'


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
  return (
    <AppContainer>
      <HomePage />
    </AppContainer>
  )
}

export default App
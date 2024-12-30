import React from 'react'
import styled from 'styled-components'
import { motion } from 'framer-motion'
import { FaChartLine, FaCoins, FaTools, FaFileContract } from 'react-icons/fa'

const ResourcesSection = styled.section`
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

const Grid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  margin-top: 3rem;
`

const ResourceCard = styled(motion.a)`
  background: rgba(18, 18, 26, 0.9);
  padding: 2rem;
  border-radius: 10px;
  text-decoration: none;
  color: white;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
`

const IconWrapper = styled.div`
  font-size: 2.5rem;
  color: #00f2ff;
  margin-bottom: 1rem;
`

const ResourceTitle = styled.h3`
  font-size: 1.5rem;
  margin-bottom: 1rem;
  color: #ffffff;
`

const ResourceDescription = styled.p`
  font-size: 1rem;
  color: #888;
  line-height: 1.6;
`

const Resources = () => {
  const resources = [
    {
      icon: <FaChartLine />,
      title: 'Dex Screener',
      description: 'Chart $OVERDOSE on DexScreener',
      url: 'https://dexscreener.com/ethereum/0x8fbce1ab5ee29aada1b716cb3d09ed61f7657668'
    },
    {
      icon: <FaTools />,
      title: 'DexTools',
      description: 'Trade $OVERDOSE on DexTools',
      url: 'https://www.dextools.io/app/en/ether/pair-explorer/0x8fbce1ab5ee29aada1b716cb3d09ed61f7657668'
    },
    {
      icon: <FaFileContract />,
      title: 'Contract',
      description: '2722Zpk2jDLFjKdqeFe1GBgYxN1SLR3ioVNiojrppump',
      url: 'https://solscan.io/address/2722Zpk2jDLFjKdqeFe1GBgYxN1SLR3ioVNiojrppump'
    }
  ]

  return (
    <ResourcesSection>
      <Container>
        <Title
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
        >
          Essential Tools
        </Title>
        <Grid>
          {resources.map((resource, index) => (
            <ResourceCard
              key={index}
              href={resource.url}
              target="_blank"
              rel="noopener noreferrer"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, delay: index * 0.2 }}
              whileHover={{ 
                scale: 1.05,
                boxShadow: '0 5px 20px rgba(0, 242, 255, 0.3)'
              }}
            >
              <IconWrapper>{resource.icon}</IconWrapper>
              <ResourceTitle>{resource.title}</ResourceTitle>
              <ResourceDescription>{resource.description}</ResourceDescription>
            </ResourceCard>
          ))}
        </Grid>
      </Container>
    </ResourcesSection>
  )
}

export default Resources
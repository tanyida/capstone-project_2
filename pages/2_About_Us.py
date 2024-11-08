import streamlit as st

# region <--------- Streamlit App Configuration --------->
st.set_page_config(
    layout="centered",
    page_title="My Streamlit App"
)

# endregion <--------- Streamlit App Configuration --------->

st.title("About Us")

st.markdown("""
            
# User case 1 - WSHO Officer Assessment
## Project Scope
The scope of this project is to assist MOM officers in the Licensing Department to summarise and validate the responses from WSHO Applicants. 
The MOM Licensing branch, operating under PICS (Planning, Info & Corp Services) within OSHD, is responsible for evaluating and approving applications for the registrations of WSHOs 
(Workplace Safety and Health Officer). As part of the assessment criteria, applicants are required to complete the Professional Work Review Write-up Form.")

## Objectives
In the process of assessing an applicant’s suitability, officers from the Licensing Branch will have to manually review and evaluate “Section E: Demonstration of WSH Experience” within the assessment form. 

In this section, applicants are required to demonstrate their WSH experience and knowledge by accurately citing examples of Section/Regulation No. for the following WSH legislations. 

The objective of this App is to assist the officers to efficiently assess the Workplace Safety and Health Officer (WSHO) Applicants by summarising applicants’ responses.

## Available Data

The data used are the regulation documents containing the WSH legislations. 
Below are a few examples of the Regulatory documents: 
- Workplace Safety and Health (General Provisions) Regulations: https://sso.agc.gov.sg/SL/WSHA2006-RG1.
- Workplace Safety and Health (Incident Reporting) Regulations: https://sso.agc.gov.sg/SL-Supp/S735-2020/Published/20200831?DocDate=20200831         

## Features

- Crosscheck user's inputs with the uploaded document and validate if the details of the inputs are factual and correct.    

# User case 2 - Virtual safety assistant for Video surveillance system (VSS)
## Project Scope
With the recent changes in the framework of regulatory requirements for construction projects in Singapore, 
the scope of this project is to assist construction project managers in their queries in finding out if 
they need to install video surveillance system in their workplaces.")

## Objective
For workplace safety and health purposes, from 1 June 2024, all construction worksites with a contract value of $5 million and above are required to install VSS 
The objective of the chatbot is to assist project managers or related personnel in answering their queries regarding the requirements.
.

## Available Data

The data used are the FAQ document containing the questions and answers on the VSS installation requirements for construction projects.
            
## Features
- Verifies user's question regarding VSS and answer the queries.    

""")
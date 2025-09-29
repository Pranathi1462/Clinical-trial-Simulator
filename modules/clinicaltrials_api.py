import requests
import json
import re
from urllib.parse import quote

class ClinicalTrialsAPI:
    def __init__(self):
        self.base_url = "https://clinicaltrials.gov/api/v2/studies"
        self.headers = {
            "User-Agent": "Clinical-Trial-AI-Simulator/1.0",
            "Accept": "application/json"
        }
    
    def fetch_study(self, nct_id):
        """
        Fetch study data from ClinicalTrials.gov API
        
        Args:
            nct_id (str): NCT identifier (e.g., 'NCT04567890')
            
        Returns:
            dict: Study data or None if not found
        """
        if not nct_id:
            raise ValueError("NCT ID is required")
        
        # Clean and validate NCT ID
        nct_id = self._clean_nct_id(nct_id)
        if not self._validate_nct_id(nct_id):
            raise ValueError(f"Invalid NCT ID format: {nct_id}")
        
        try:
            # Construct API URL
            url = f"{self.base_url}/{nct_id}"
            
            # Add query parameters for detailed information
            params = {
                "fields": "NCTId,BriefTitle,OfficialTitle,BriefSummary,DetailedDescription,"
                         "EligibilityCriteria,PrimaryOutcome,SecondaryOutcome,StudyType,"
                         "Phase,EnrollmentCount,StudyFirstSubmitDate,CompletionDate,"
                         "Condition,InterventionName,InterventionDescription,SponsorName,"
                         "StudyDesign,MinimumAge,MaximumAge,Gender,HealthyVolunteers"
            }
            
            # Make API request
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_study_response(data)
            elif response.status_code == 404:
                raise Exception(f"Study not found: {nct_id}")
            else:
                raise Exception(f"API request failed with status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error while fetching study: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response from API: {str(e)}")
    
    def search_studies(self, query, max_results=10):
        """
        Search for studies using query terms
        
        Args:
            query (str): Search query
            max_results (int): Maximum number of results to return
            
        Returns:
            list: List of study summaries
        """
        if not query or not query.strip():
            raise ValueError("Search query is required")
        
        try:
            # Construct search URL
            url = f"{self.base_url}"
            
            params = {
                "query.term": query,
                "pageSize": min(max_results, 1000),  # API limit
                "fields": "NCTId,BriefTitle,Phase,StudyType,Condition,OverallStatus"
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_search_response(data)
            else:
                raise Exception(f"Search request failed with status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error during search: {str(e)}")
    
    def fetch_study_eligibility(self, nct_id):
        """
        Fetch only eligibility criteria for a study
        
        Args:
            nct_id (str): NCT identifier
            
        Returns:
            dict: Eligibility criteria data
        """
        study_data = self.fetch_study(nct_id)
        if study_data:
            return {
                "nct_id": nct_id,
                "title": study_data.get("title"),
                "eligibility_criteria": study_data.get("eligibility_criteria"),
                "minimum_age": study_data.get("minimum_age"),
                "maximum_age": study_data.get("maximum_age"),
                "gender": study_data.get("gender"),
                "healthy_volunteers": study_data.get("healthy_volunteers")
            }
        return None
    
    def format_study_for_analysis(self, study_data):
        """
        Format study data into text suitable for AI analysis
        
        Args:
            study_data (dict): Study data from API
            
        Returns:
            str: Formatted text for analysis
        """
        if not study_data:
            return ""
        
        sections = []
        
        # Title and basic info
        if study_data.get("title"):
            sections.append(f"STUDY TITLE: {study_data['title']}")
        
        if study_data.get("nct_id"):
            sections.append(f"NCT ID: {study_data['nct_id']}")
        
        # Study phase and type
        if study_data.get("phase"):
            sections.append(f"PHASE: {study_data['phase']}")
        
        if study_data.get("study_type"):
            sections.append(f"STUDY TYPE: {study_data['study_type']}")
        
        # Brief summary
        if study_data.get("brief_summary"):
            sections.append(f"BRIEF SUMMARY:\n{study_data['brief_summary']}")
        
        # Detailed description
        if study_data.get("detailed_description"):
            sections.append(f"DETAILED DESCRIPTION:\n{study_data['detailed_description']}")
        
        # Eligibility criteria
        if study_data.get("eligibility_criteria"):
            sections.append(f"ELIGIBILITY CRITERIA:\n{study_data['eligibility_criteria']}")
        
        # Age and gender requirements
        age_info = []
        if study_data.get("minimum_age"):
            age_info.append(f"Minimum Age: {study_data['minimum_age']}")
        if study_data.get("maximum_age"):
            age_info.append(f"Maximum Age: {study_data['maximum_age']}")
        if study_data.get("gender"):
            age_info.append(f"Gender: {study_data['gender']}")
        
        if age_info:
            sections.append("DEMOGRAPHIC REQUIREMENTS:\n" + "\n".join(age_info))
        
        # Primary outcomes
        if study_data.get("primary_outcomes"):
            outcomes = []
            for outcome in study_data["primary_outcomes"]:
                if isinstance(outcome, dict):
                    outcomes.append(f"- {outcome.get('measure', 'Unknown measure')}")
                else:
                    outcomes.append(f"- {outcome}")
            sections.append("PRIMARY OUTCOMES:\n" + "\n".join(outcomes))
        
        # Secondary outcomes
        if study_data.get("secondary_outcomes"):
            outcomes = []
            for outcome in study_data["secondary_outcomes"]:
                if isinstance(outcome, dict):
                    outcomes.append(f"- {outcome.get('measure', 'Unknown measure')}")
                else:
                    outcomes.append(f"- {outcome}")
            sections.append("SECONDARY OUTCOMES:\n" + "\n".join(outcomes))
        
        # Interventions
        if study_data.get("interventions"):
            interventions = []
            for intervention in study_data["interventions"]:
                if isinstance(intervention, dict):
                    name = intervention.get("name", "Unknown intervention")
                    description = intervention.get("description", "")
                    interventions.append(f"- {name}: {description}")
                else:
                    interventions.append(f"- {intervention}")
            sections.append("INTERVENTIONS:\n" + "\n".join(interventions))
        
        # Conditions
        if study_data.get("conditions"):
            if isinstance(study_data["conditions"], list):
                conditions = "\n".join([f"- {condition}" for condition in study_data["conditions"]])
            else:
                conditions = f"- {study_data['conditions']}"
            sections.append(f"CONDITIONS:\n{conditions}")
        
        # Sponsor
        if study_data.get("sponsor"):
            sections.append(f"SPONSOR: {study_data['sponsor']}")
        
        return "\n\n".join(sections)
    
    def _clean_nct_id(self, nct_id):
        """Clean and standardize NCT ID format"""
        if not nct_id:
            return ""
        
        # Remove whitespace and convert to uppercase
        nct_id = nct_id.strip().upper()
        
        # Add NCT prefix if missing
        if not nct_id.startswith("NCT"):
            nct_id = "NCT" + nct_id
        
        return nct_id
    
    def _validate_nct_id(self, nct_id):
        """Validate NCT ID format"""
        # NCT ID should be NCT followed by 8 digits
        pattern = r"^NCT\d{8}$"
        return bool(re.match(pattern, nct_id))
    
    def _parse_study_response(self, api_response):
        """Parse study response from ClinicalTrials.gov API"""
        if not api_response or "studies" not in api_response:
            return None
        
        studies = api_response["studies"]
        if not studies:
            return None
        
        study = studies[0]  # Get first (and should be only) study
        protocol_section = study.get("protocolSection", {})
        
        # Extract identification info
        identification = protocol_section.get("identificationModule", {})
        
        # Extract design info
        design = protocol_section.get("designModule", {})
        
        # Extract arms/interventions info
        arms_interventions = protocol_section.get("armsInterventionsModule", {})
        
        # Extract eligibility info
        eligibility = protocol_section.get("eligibilityModule", {})
        
        # Extract outcomes info
        outcomes = protocol_section.get("outcomesModule", {})
        
        # Extract conditions info
        conditions = protocol_section.get("conditionsModule", {})
        
        # Extract sponsor info
        sponsor = protocol_section.get("sponsorCollaboratorsModule", {})
        
        # Parse and structure the data
        parsed_study = {
            "nct_id": identification.get("nctId"),
            "title": identification.get("briefTitle") or identification.get("officialTitle"),
            "brief_summary": identification.get("briefSummary", {}).get("textblock"),
            "detailed_description": identification.get("detailedDescription", {}).get("textblock"),
            "phase": design.get("phases", [None])[0] if design.get("phases") else None,
            "study_type": design.get("studyType"),
            "enrollment_count": design.get("enrollmentInfo", {}).get("count"),
            "eligibility_criteria": eligibility.get("eligibilityCriteria"),
            "minimum_age": eligibility.get("minimumAge"),
            "maximum_age": eligibility.get("maximumAge"),
            "gender": eligibility.get("sex"),
            "healthy_volunteers": eligibility.get("healthyVolunteers"),
            "primary_outcomes": outcomes.get("primaryOutcomes", []),
            "secondary_outcomes": outcomes.get("secondaryOutcomes", []),
            "conditions": conditions.get("conditions", []),
            "interventions": arms_interventions.get("interventions", []),
            "sponsor": sponsor.get("leadSponsor", {}).get("name")
        }
        
        return parsed_study
    
    def _parse_search_response(self, api_response):
        """Parse search response from ClinicalTrials.gov API"""
        if not api_response or "studies" not in api_response:
            return []
        
        studies = api_response["studies"]
        parsed_studies = []
        
        for study in studies:
            protocol_section = study.get("protocolSection", {})
            identification = protocol_section.get("identificationModule", {})
            design = protocol_section.get("designModule", {})
            status = protocol_section.get("statusModule", {})
            conditions = protocol_section.get("conditionsModule", {})
            
            parsed_study = {
                "nct_id": identification.get("nctId"),
                "title": identification.get("briefTitle"),
                "phase": design.get("phases", [None])[0] if design.get("phases") else None,
                "study_type": design.get("studyType"),
                "overall_status": status.get("overallStatus"),
                "conditions": conditions.get("conditions", [])
            }
            
            parsed_studies.append(parsed_study)
        
        return parsed_studies

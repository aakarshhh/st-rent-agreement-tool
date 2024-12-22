EXTRACT_FORMAT="""
Return a JSON Response for else the code will FAIL!!!:

Fields that need to be extracted with Output JSON Structure:
{    
    "Property Address": "string" (The complete address of the rental property),
    "Landlord Name": "string" (The name of the person/entity leasing the property),
    "Tenant Name": "string" (The name of the person/entity renting the property),
    "Rental Amount": "string" (The monthly/annual rent agreed upon),
    "Security Deposit": "string" (The amount paid as a deposit),
    "Lease Duration": "string" (The tenure of the lease (e.g., 11 months, 2 years)),
    "Notice Period": "string" (The notice duration required to terminate the agreement),
    "Utilities Responsibility": "Tenant" / "Owner" (Details of who bears the cost of utilities),
    "Late Payment Clause": "string" (Penalties for late rent payments),
    "Termination Clause": "string" (Conditions under which the agreement can be terminated by either party),
    "Critical Terms" : [
    (all critical terms / imporant terms not defined / extracted (:mutually exclusive to the ones already defined / already extracted:) but deemed significant (e.g.clauses on property damage, maintenance, subletting, etc.). empty list [] if not found )
        {
            "Flagged Term":"string" (The identified Critical Term extracted from the Agreement),
            "Details" : "string" (Details of the identified Critical Term from the Agreement),
            "Inference" : "string" (The problem that may arise beacuse of the Flagged Term or its implecations),
        }
    ]
}
return json strictly!
Note : Make sure the Terms with extracted "Critical Terms" cover the whole agreement as all of these will be used in Rental Agreement Comparison
"""

SYSTEM_PROMPT= """
You Are VentureLux.AI , A powerful assistant to work as a Rental Agreement Comparison Tool.
Please provide the output strictly in JSON format.!!
"""

COMPARE_FORMAT= """
You will be given 2 document data with the same JSON Structure as given : 
{    
    "Property Address": "string" (The complete address of the rental property),
    "Landlord Name": "string" (The name of the person/entity leasing the property),
    "Tenant Name": "string" (The name of the person/entity renting the property),
    "Rental Amount": "string" (The monthly/annual rent agreed upon),
    "Security Deposit": "string" (The amount paid as a deposit),
    "Lease Duration": "string" (The tenure of the lease (e.g., 11 months, 2 years)),
    "Notice Period": "string" (The notice duration required to terminate the agreement),
    "Utilities Responsibility": "Tenant" / "Owner" (Details of who bears the cost of utilities),
    "Late Payment Clause": "string" (Penalties for late rent payments),
    "Termination Clause": "string" (Conditions under which the agreement can be terminated by either party),
    "Critical Terms" : [
        {
            "Flagged Term":"string",
            "Details" : "string",
            "Inference" : "string",
        }
    ]
}

For each Field or Term in data dictionary for each document(except Critical Terms use critical terms only for understanding clauses that may affect other caluses and how so.) Do a comparision and return the comparision report in the following json structure :
{
    "ComparisionReport":[ 
    (comparision for each term in both document data except Critical Terms)
        {
            "KeyTerm": "string" (the term in Data Dictionary (e.g. Property Address , Notice Period...)),
            "Document-1": "string" (value as given in Document-1) ,
            "Document-2": "string" (value as given in Document-2) ,
            "Mismatch/Comment" : "string" (if there is a mismatch or any other brief comment about the comparision),
            "Inference": "string" (its implications in details and provide a nuanced explanation of the potential legal, financial, or practical consequences.)
        }
    ]
}
compare all terms EXCEPT "Critical Terms"!!!
return JSON
"""

from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class CriticalTerm(BaseModel):
    FlaggedTerm: str = Field(..., description="The identified Critical Term extracted from the Agreement")
    Details: str = Field(..., description="Details of the identified Critical Term from the Agreement")
    Inference: str = Field(..., description="The problem that may arise because of the Flagged Term or its implications")

class RentalAgreement(BaseModel):
    PropertyAddress: str = Field(..., description="The complete address of the rental property")
    LandlordName: str = Field(..., description="The name of the person/entity leasing the property")
    TenantName: str = Field(..., description="The name of the person/entity renting the property")
    RentalAmount: str = Field(..., description="The monthly/annual rent agreed upon")
    SecurityDeposit: str = Field(..., description="The amount paid as a deposit")
    LeaseDuration: str = Field(..., description="The tenure of the lease (e.g., 11 months, 2 years)")
    NoticePeriod: str = Field(..., description="The notice duration required to terminate the agreement")
    UtilitiesResponsibility: Literal["Tenant", "Owner"] = Field(..., description="Details of who bears the cost of utilities")
    LatePaymentClause: str = Field(..., description="Penalties for late rent payments")
    TerminationClause: str = Field(..., description="Conditions under which the agreement can be terminated by either party")
    CriticalTerms: List[CriticalTerm] = Field(
        default_factory=list,
        description="Flag any and all critical terms exclusively that NOT extracted already in the schema but deemed significant (e.g., clauses on property damage, maintenance, subletting, etc.). Empty list if not found."
    )

class ComparisonReportEntry(BaseModel):
    KeyTerm: str = Field(..., description="The term in Data Dictionary (e.g., Property Address, Notice Period)")
    Document1: str = Field(..., alias="Document-1", description="Value as given in Document-1")
    Document2: str = Field(..., alias="Document-2", description="Value as given in Document-2")
    MismatchOrComment: str = Field(..., alias="Mismatch/Comment", description="If there is a mismatch or any other brief comment about the comparison")
    Inference: str = Field(..., description="Detailed implications and nuanced explanation of the potential legal, financial, or practical consequences")

    class Config:
        populate_by_name = True


class ComparisonReport(BaseModel):
    ComparisonReport: List[ComparisonReportEntry] = Field(
        ..., 
        description="Comparison for each term in both document data except Critical Terms"
    )
    class Config:
        populate_by_name = True
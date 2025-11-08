"""
Sample data generator for WhatsApp Bulk Contact Manager
Creates Excel files with sample contacts for testing
"""

import pandas as pd
import random

# Sample data for different regions and formats
BRAZILIAN_NAMES = [
    "João Silva", "Maria Santos", "Pedro Oliveira", "Ana Costa", "Carlos Souza",
    "Lucia Ferreira", "Marcos Rodrigues", "Sandra Almeida", "Paulo Lima", "Julia Gomes",
    "Ricardo Barbosa", "Fernanda Rocha", "Diego Nascimento", "Camila Martins", "André Araújo",
    "Patricia Moreira", "Bruno Carvalho", "Renata Castro", "Felipe Pinto", "Vanessa Ribeiro",
    "Gustavo Correia", "Amanda Monteiro", "Rodrigo Vieira", "Bruna Duarte", "Leonardo Mendes",
    "Tatiana Nunes", "Eduardo Sousa", "Priscila Sales", "Rafael Teixeira", "Carolina Moraes",
    "Thiago Borges", "Natália Andrade", "Vinícius Pires", "Letícia Abreu", "Henrique Campos",
    "Larissa Cardoso", "Murilo Moura", "Júlia Rezende", "César Lima", "Marina Freitas",
    "Daniel Santiago", "Bianca Queirós", "Gabriel Lemos", "Vitória Guerra", "Lucas Farias",
    "Isabela Melo", "Matheus Peixoto", "Helena Azevedo", "Pedro Henrique", "Manuela Cunha"
]

BRAZILIAN_PHONES = [
    "(11) 98765-4321", "(21) 99876-5432", "(31) 91234-5678", "(41) 92345-6789", "(51) 93456-7890",
    "(61) 94567-8901", "(71) 95678-9012", "(81) 96789-0123", "(91) 97890-1234", "(11) 98901-2345",
    "(21) 99012-3456", "(31) 90123-4567", "(41) 91234-5678", "(51) 92345-6789", "(61) 93456-7890",
    "(71) 94567-8901", "(81) 95678-9012", "(91) 96789-0123", "(11) 97890-1234", "(21) 98901-2345",
    "11987654321", "21998765432", "31912345678", "41923456789", "51934567890",
    "61945678901", "71956789012", "81967890123", "91978901234", "11989012345",
    "+55 11 98765-4321", "+55 21 99876-5432", "+55 31 91234-5678", "+55 41 92345-6789", "+55 51 93456-7890",
    "55 61 94567-8901", "55 71 95678-9012", "55 81 96789-0123", "55 91 97890-1234", "55 11 98901-2345"
]

INTERNATIONAL_NAMES = [
    "John Smith", "Emma Johnson", "Michael Brown", "Sophia Davis", "James Wilson",
    "Olivia Miller", "Robert Taylor", "Ava Anderson", "David Thomas", "Isabella Garcia",
    "William Martinez", "Mia Robinson", "Richard Clark", "Charlotte Rodriguez", "Joseph Lewis",
    "Amelia Lee", "Christopher Walker", "Harper Hall", "Daniel Allen", "Evelyn Young",
    "Matthew King", "Abigail Wright", "Andrew Scott", "Emily Lopez", "Joshua Hill",
    "Elizabeth Green", "Ryan Adams", "Sofia Baker", "Jacob Nelson", "Avery Mitchell",
    "Nicholas Perez", "Ella Roberts", "Jonathan Turner", "Scarlett Phillips", "Noah Campbell",
    "Grace Parker", "Christian Evans", "Victoria Edwards", "Samuel Collins", "Chloe Stewart",
    "Benjamin Sanchez", "Camila Morris", "Alexander Rogers", "Aria Reed", "Logan Cook",
    "Penelope Morgan", "Caleb Bell", "Layla Murphy", "Dylan Bailey", "Riley Rivera"
]

INTERNATIONAL_PHONES = [
    "+1-555-0123", "+1-555-0124", "+1-555-0125", "+1-555-0126", "+1-555-0127",
    "+44-20-1234-5678", "+44-20-1234-5679", "+44-20-1234-5680", "+44-20-1234-5681", "+44-20-1234-5682",
    "+49-30-12345678", "+49-30-12345679", "+49-30-12345680", "+49-30-12345681", "+49-30-12345682",
    "555-0128", "555-0129", "555-0130", "555-0131", "555-0132",
    "+1 (555) 0133", "+1 (555) 0134", "+1 (555) 0135", "+1 (555) 0136", "+1 (555) 0137",
    "555.0138", "555.0139", "555.0140", "555.0141", "555.0142"
]

def create_sample_excel(filename: str, num_contacts: int = 50, region: str = "brazil", include_errors: bool = False):
    """Create sample Excel file with contacts"""
    
    if region.lower() == "brazil":
        names = BRAZILIAN_NAMES
        phones = BRAZILIAN_PHONES
    else:
        names = INTERNATIONAL_NAMES
        phones = INTERNATIONAL_PHONES
    
    # Generate sample data
    data = []
    for i in range(num_contacts):
        name = random.choice(names)
        phone = random.choice(phones)
        
        # Add some variations and custom fields
        contact = {
            "Name": name,
            "Phone": phone,
            "Email": f"{name.lower().replace(' ', '.')}@example.com",
            "Company": f"Company {random.randint(1, 20)}",
            "City": f"City {random.randint(1, 10)}",
            "Notes": f"Sample contact {i + 1}"
        }
        
        # Introduce some errors if requested
        if include_errors and random.random() < 0.1:  # 10% error rate
            error_type = random.choice(["missing_name", "missing_phone", "invalid_phone", "extra_chars"])
            
            if error_type == "missing_name":
                contact["Name"] = ""
            elif error_type == "missing_phone":
                contact["Phone"] = ""
            elif error_type == "invalid_phone":
                contact["Phone"] = "123"  # Invalid phone
            elif error_type == "extra_chars":
                contact["Phone"] = "ABC" + contact["Phone"] + "XYZ"
        
        data.append(contact)
    
    # Create DataFrame and save to Excel
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    print(f"Created {filename} with {num_contacts} contacts")

def create_csv_sample(filename: str, num_contacts: int = 50):
    """Create sample CSV file"""
    
    names = BRAZILIAN_NAMES[:num_contacts]
    phones = BRAZILIAN_PHONES[:num_contacts]
    
    data = []
    for i in range(num_contacts):
        contact = {
            "Nome": names[i % len(names)],
            "Telefone": phones[i % len(phones)],
            "Email": f"contact{i+1}@example.com",
            "Cidade": f"Cidade {random.randint(1, 5)}"
        }
        data.append(contact)
    
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Created {filename} with {num_contacts} contacts")

if __name__ == "__main__":
    # Create sample files
    print("Creating sample data files...")
    
    # Main sample files
    create_sample_excel("sample_50_contacts.xlsx", 50, "brazil")
    create_sample_excel("sample_with_errors.xlsx", 50, "brazil", include_errors=True)
    create_sample_excel("sample_large_5000.xlsx", 5000, "international")
    create_csv_sample("sample_contacts.csv", 100)
    
    # Additional test files
    create_sample_excel("brazilian_contacts.xlsx", 100, "brazil")
    create_sample_excel("international_contacts.xlsx", 100, "international")
    
    print("\nSample files created successfully!")
    print("\nFiles created:")
    print("- sample_50_contacts.xlsx (50 valid Brazilian contacts)")
    print("- sample_with_errors.xlsx (50 contacts with some errors)")
    print("- sample_large_5000.xlsx (5000 international contacts)")
    print("- sample_contacts.csv (100 contacts in CSV format)")
    print("- brazilian_contacts.xlsx (100 Brazilian contacts)")
    print("- international_contacts.xlsx (100 international contacts)")
"""
STEP 3: Unstructured Knowledge Base Builder
Compiles all admission portal data, detailed fees, seat matrices, placement records,
and eligibility criteria into `unstructured_admission_data.json`.
"""
import os
import json

UNSTRUCTURED_DATA_JSON = "unstructured_admission_data.json"

def build_knowledge_base():
    chunks = []
    chunk_counter = 1

    # 1. B.Tech Fees
    btech_fees = [
        {"branch": "Computer Science and Engineering (CSE) and CSE (AI & ML)", "sem1": "₹108,125", "sem2": "₹77,825", "sem3_6": "₹97,825", "sem7": "₹98,325", "sem8": "₹99,325", "total_4yr": "₹7,74,900"},
        {"branch": "CSE (Data Science)", "sem1": "₹99,625", "sem2": "₹69,325", "sem3_6": "₹89,325", "sem7": "₹89,825", "sem8": "₹90,825", "total_4yr": "₹7,06,900"},
        {"branch": "Information Technology (IT), Computer Science & Technology (CST), CSE (Business Systems - CSBS)", "sem1": "₹96,375", "sem2": "₹66,075", "sem3_6": "₹86,075", "sem7": "₹86,575", "sem8": "₹87,575", "total_4yr": "₹6,80,900"},
        {"branch": "Electronics and Communications Engineering (ECE)", "sem1": "₹92,625", "sem2": "₹62,325", "sem3_6": "₹82,325", "sem7": "₹82,825", "sem8": "₹83,825", "total_4yr": "₹6,50,900"},
        {"branch": "Electrical Engineering (EE)", "sem1": "₹71,125", "sem2": "₹40,825", "sem3_6": "₹60,825", "sem7": "₹61,325", "sem8": "₹62,325", "total_4yr": "₹4,78,900"},
        {"branch": "Civil Engineering (CE) and Mechanical Engineering (ME)", "sem1": "₹67,625", "sem2": "₹37,325", "sem3_6": "₹57,325", "sem7": "₹57,825", "sem8": "₹58,825", "total_4yr": "₹4,50,900"},
        {"branch": "Electronics and Computer Science (ECS)", "sem1": "₹79,375", "sem2": "₹49,075", "sem3_6": "₹69,075", "sem7": "₹69,575", "sem8": "₹70,575", "total_4yr": "₹5,44,900"}
    ]
    for item in btech_fees:
        content_str = (
            f"B.Tech Fee Structure for {item['branch']} at Narula Institute of Technology:\n"
            f"• 1st Semester Fee (Payable at Admission): {item['sem1']}\n"
            f"• 2nd Semester Fee: {item['sem2']}\n"
            f"• 3rd, 4th, 5th, and 6th Semester Fees: {item['sem3_6']} per semester\n"
            f"• 7th Semester Fee: {item['sem7']} | 8th Semester Fee: {item['sem8']}\n"
            f"• Total 4-Year Program Fee (8 Semesters): {item['total_4yr']}\n"
            "Uniform fee (₹6,000) and MAKAUT semester exam fees are payable separately."
        )
        chunks.append({
            "chunk_id": f"chunk_{chunk_counter:05d}",
            "intent": "fee",
            "category": "btech_fee",
            "title": f"B.Tech 1st Semester & 4-Year Fee Structure for {item['branch']}",
            "content": content_str,
            "metadata": {"branch": item["branch"], "sem1_fee": item["sem1"], "total_fee": item["total_4yr"]}
        })
        chunk_counter += 1

    # 1b. B.Tech Lateral Entry (Direct 2nd Year) Fees
    lateral_fees = [
        {"branch": "Lateral Entry CSE, CSE (AIML), IT, CSE (DS), CST, CSBS", "sem3": "₹93,425", "sem4_6": "₹63,675", "sem7": "₹64,175", "sem8": "₹65,175", "total_3yr": "₹4,13,800"},
        {"branch": "Lateral Entry ECE", "sem3": "₹88,175", "sem4_6": "₹58,425", "sem7": "₹58,925", "sem8": "₹59,925", "total_3yr": "₹3,82,300"},
        {"branch": "Lateral Entry EE, CE, ME", "sem3": "₹77,175", "sem4_6": "₹47,425", "sem7": "₹47,925", "sem8": "₹48,925", "total_3yr": "₹3,16,300"},
        {"branch": "Lateral Entry ECS", "sem3": "₹86,425", "sem4_6": "₹56,675", "sem7": "₹57,175", "sem8": "₹58,175", "total_3yr": "₹3,71,800"}
    ]
    for item in lateral_fees:
        chunks.append({
            "chunk_id": f"chunk_{chunk_counter:05d}",
            "intent": "fee",
            "category": "lateral_fee",
            "title": f"B.Tech Lateral Entry (2nd Year) Fee Structure for {item['branch']}",
            "content": (
                f"B.Tech Lateral Entry Fee Structure for {item['branch']} (Direct 2nd Year / 3-Year Degree):\n"
                f"• 3rd Semester Fee (Payable at Admission): {item['sem3']}\n"
                f"• 4th, 5th, and 6th Semester Fees: {item['sem4_6']} per semester\n"
                f"• 7th Semester Fee: {item['sem7']} | 8th Semester Fee: {item['sem8']}\n"
                f"• Total 3-Year Program Fee (6 Semesters): {item['total_3yr']}\n"
                "Eligibility: Diploma in Engineering or B.Sc with valid WB-JELET rank."
            ),
            "metadata": {"branch": item["branch"], "admission_fee": item["sem3"], "total": item["total_3yr"]}
        })
        chunk_counter += 1

    # 1c. BCA, BBA, Diploma & PG (MCA / M.Tech) Fees
    other_fees = [
        ("Bachelor of Computer Applications (BCA)", "1st Sem: ₹68,200 | 2nd-5th Sem: ₹49,500/sem | 6th Sem: ₹51,000 | Total (3 Yrs): ₹4,16,700"),
        ("Bachelor of Business Administration (BBA)", "1st Sem: ₹60,300 | 2nd-5th Sem: ₹41,600/sem | 6th Sem: ₹43,100 | Total (3 Yrs): ₹3,53,500"),
        ("Diploma in Engineering (Counseling & Direct)", "Counseling: 1st Sem ₹33,600, 2nd-6th Sem ₹16,000/sem (Total ₹1,14,100) | Direct: 1st Sem ₹33,600, 2nd-6th Sem ₹18,000/sem (Total ₹1,24,100)"),
        ("Master of Computer Applications (MCA - 2 Years)", "1st Sem: ₹87,100 | 2nd Sem: ₹73,000 | 3rd Sem: ₹73,500 | 4th Sem: ₹74,500 | Total (2 Yrs): ₹3,08,100"),
        ("Master of Technology (M.Tech - 2 Years)", "1st Sem: ₹77,008 | 2nd Sem: ₹50,000 | 3rd Sem: ₹51,000 | 4th Sem: ₹52,592 | Total (2 Yrs): ₹2,30,600")
    ]
    for prog_name, fee_desc in other_fees:
        chunks.append({
            "chunk_id": f"chunk_{chunk_counter:05d}",
            "intent": "fee",
            "category": "program_fee",
            "title": f"Fee Structure for {prog_name}",
            "content": f"Fee Structure for {prog_name} at Narula Institute of Technology:\n{fee_desc}",
            "metadata": {"program": prog_name}
        })
        chunk_counter += 1

    # 2. Hostel & Uniform
    chunks.append({
        "chunk_id": f"chunk_{chunk_counter:05d}",
        "intent": "hostel",
        "category": "hostel_fees",
        "title": "Hostel Fees, Food Mess, and Uniform Charges at Narula Institute of Technology",
        "content": (
            "Hostel and Facility Charges at Narula Institute of Technology:\n"
            "• Hostel Fees: ₹6,500 per month (6 months semester = ₹39,000) plus one-time admission fee of ₹5,000. Total payable at admission is ₹44,000.\n"
            "• Hostel Facilities: Separate secure hostels for boys and girls, 24/7 security, Wi-Fi, power backup, and hygienic mess food (veg & non-veg).\n"
            "• Uniform Charges: ₹6,000 one-time for B.Tech, BCA, BBA, and Diploma students (₹2,500 for MCA & M.Tech).\n"
            "• Payment Terms: All fees must be paid through online portal only. EMI and education loan assistance available."
        ),
        "metadata": {"hostel_sem": "₹44,000", "uniform": "₹6,000"}
    })
    chunk_counter += 1

    # 3. Placement Records & Career Statistics
    chunks.append({
        "chunk_id": f"chunk_{chunk_counter:05d}",
        "intent": "placement",
        "category": "placements",
        "title": "Campus Placements, Highest Package, Average Salary, and Placement Percentage at Narula Institute of Technology",
        "content": (
            "Campus Placement Statistics and Recruiter Records at Narula Institute of Technology (NIT):\n"
            "• Overall Placement Percentage: 88%+ consistent placement rate across engineering and technology departments.\n"
            "• Highest Salary Package: ₹18 LPA (Lakhs Per Annum).\n"
            "• Average Salary Package: ₹5.2 LPA.\n"
            "• Total Offers: 1000+ job offers generated for eligible graduates.\n"
            "• Top Recruiters: Tata Consultancy Services (TCS), Cognizant, Wipro, Capgemini, Infosys, Amazon, Tech Mahindra, Mindtree, LTI, and IBM.\n"
            "• Industry Labs: Dedicated Apple iOS Developer Training Center, AI & Robotics Centers of Excellence.\n"
            "• Placement Assistance: Pre-placement soft skills training, mock interviews, and technical coding bootcamps starting from 3rd year."
        ),
        "metadata": {"placement_rate": "88%+", "highest_package": "18 LPA", "average_package": "5.2 LPA"}
    })
    chunk_counter += 1

    # 4. Seat Matrix
    stream_seats = [
        ("Computer Science and Engineering (CSE)", "300 seats", "B.Tech (UG)"),
        ("CSE (AI and Machine Learning)", "240 seats", "B.Tech (UG)"),
        ("Information Technology (IT)", "180 seats", "B.Tech (UG)"),
        ("Electronics and Communications Engineering (ECE)", "150 seats", "B.Tech (UG)"),
        ("CSE (Data Science)", "120 seats", "B.Tech (UG)"),
        ("Electrical Engineering (EE)", "60 seats", "B.Tech (UG)"),
        ("Civil Engineering (CE)", "60 seats", "B.Tech (UG)"),
        ("Mechanical Engineering (ME)", "60 seats", "B.Tech (UG)"),
        ("Computer Science and Technology (CST)", "60 seats", "B.Tech (UG)"),
        ("CSE (Business Systems - CSBS)", "60 seats", "B.Tech (UG)"),
        ("Electronics and Computer Science (ECS)", "30 seats", "B.Tech (UG)"),
        ("Master of Computer Applications (MCA)", "60 seats", "PG"),
        ("M.Tech in CSE, ECE, EE, CE", "18 seats each", "PG"),
        ("Bachelor of Computer Applications (BCA)", "120 seats", "UG"),
        ("Bachelor of Business Administration (BBA)", "60 seats", "UG"),
        ("Diploma in Engineering (Civil, Electrical, Mechanical, ETCE)", "30 to 60 seats per branch", "Diploma")
    ]
    for stream, seats, degree in stream_seats:
        chunks.append({
            "chunk_id": f"chunk_{chunk_counter:05d}",
            "intent": "seat",
            "category": "seat_matrix",
            "title": f"Seat Intake for {stream}",
            "content": f"Program: {stream}\nApproved Seat Intake: {seats}\nDegree Level: {degree}\nInstitution: Narula Institute of Technology (NIT), Kolkata",
            "metadata": {"stream": stream, "seats": seats}
        })
        chunk_counter += 1

    # 4b. Departments, Streams & Programs Summary Chunk
    chunks.append({
        "chunk_id": f"chunk_{chunk_counter:05d}",
        "intent": "seat",
        "category": "departments_overview",
        "title": "All Departments, Streams, Branches, and Courses Offered at Narula Institute of Technology (NIT)",
        "content": (
            "Departments, Branches, Streams, and Seat Distribution at Narula Institute of Technology (NIT):\n"
            "• B.Tech (UG - 11 Streams): CSE (300 seats), CSE AI & ML (240 seats), IT (180 seats), ECE (150 seats), "
            "CSE Data Science (120 seats), EE (60 seats), CE (60 seats), ME (60 seats), CST (60 seats), CSBS (60 seats), ECS (30 seats).\n"
            "• Postgraduate (PG): M.Tech in CSE, ECE, EE, CE (18 seats each) and MCA (60 seats).\n"
            "• Undergraduate Management & Computer Applications: BCA (120 seats) and BBA (60 seats).\n"
            "• Diploma / Polytechnic: Civil, Electrical, Mechanical, and ETCE (30 to 60 seats per branch).\n"
            "Total Capacity: 2000+ seats across 23+ programs and 11+ engineering/management departments."
        ),
        "metadata": {"type": "departments_overview"}
    })
    chunk_counter += 1

    # 5. Eligibility Criteria
    eligibility_info = [
        ("B.Tech Regular Programs (4 Years)", "Passed 10+2 with Physics & Mathematics along with Chemistry / Biotechnology / Biology / Computer Science. Minimum 45% marks in above subjects taken together (40% for reserved category SC/ST/OBC/PwD). Valid rank in WBJEE / JEE (Main) / CEE-AMPAI."),
        ("B.Tech Lateral Entry (2nd Year)", "Passed Diploma in Engineering/Technology with at least 45% marks (40% for SC/ST) or B.Sc Degree with Mathematics in 10+2. Valid rank in WB-JELET counseling."),
        ("MCA Program (2 Years)", "Passed BCA or B.Sc/B.Com/B.A with Mathematics at 10+2 or Graduation level with minimum 50% marks (45% for SC/ST). Valid rank in WB-JECA."),
        ("BCA and BBA (3 Years)", "Passed 10+2 from recognized board with English and Mathematics / Business Math / Statistics / Computer Application. Minimum 45% marks."),
        ("M.Tech Programs (2 Years)", "B.Tech/B.E in relevant branch with at least 60% marks or 6.5 CGPA. Valid GATE score or PGET conducted by MAKAUT.")
    ]
    for prog, elig in eligibility_info:
        chunks.append({
            "chunk_id": f"chunk_{chunk_counter:05d}",
            "intent": "eligibility",
            "category": "eligibility",
            "title": f"Eligibility Criteria and Entrance Exams for {prog}",
            "content": f"Program: {prog}\nEligibility Requirements: {elig}\nInstitution: Narula Institute of Technology (NIT)",
            "metadata": {"program": prog}
        })
        chunk_counter += 1

    # 6. Scholarships
    scholarships_data = [
        ("WBJEE Tuition Fee Waiver (TFW)", "100% Tuition Fee Waiver allotted via centralized WBJEE counseling for meritorious students whose annual family income is below ₹2.5 Lakhs."),
        ("Swami Vivekananda Merit-cum-Means (SVMCM)", "West Bengal state scholarship of ₹60,000 per year for B.Tech students who secured 60%+ in 10+2 with family income under ₹2.5 Lakhs."),
        ("Sikh Community Freeship", "Up to 50% freeship on tuition fees for students belonging to the Sikh community through Gurudwara verification.")
    ]
    for name, details in scholarships_data:
        chunks.append({
            "chunk_id": f"chunk_{chunk_counter:05d}",
            "intent": "scholarship",
            "category": "scholarship",
            "title": f"Scholarship Scheme: {name}",
            "content": f"Scholarship Name: {name}\nDetails & Benefits: {details}\nInstitution: Narula Institute of Technology (NIT)",
            "metadata": {"scholarship": name}
        })
        chunk_counter += 1

    # 7. Document Checklist
    chunks.append({
        "chunk_id": f"chunk_{chunk_counter:05d}",
        "intent": "document",
        "category": "documents",
        "title": "Mandatory Documents Required for Admission and Physical Verification",
        "content": (
            "Mandatory Document Checklist for Physical Verification at Narula Institute of Technology:\n"
            "1. WBJEE / JEE Main / JELET / JECA Rank Card\n"
            "2. Provisional Seat Allotment Letter from Centralized Counseling\n"
            "3. 10th Standard Admit Card / Birth Certificate (Proof of Age)\n"
            "4. 10th and 12th Standard Mark sheets and Passing Certificates\n"
            "5. Domicile Certificate (for West Bengal domicile quota / TFW / SVMCM)\n"
            "6. Category / Caste Certificate (SC/ST/OBC-A/OBC-B/PwD if applicable)\n"
            "7. Family Income Certificate (issued by SDO/BDO for SVMCM/TFW)\n"
            "8. Medical Fitness Certificate and Eye Test Certificate\n"
            "9. 5 Passport Size Color Photographs\n"
            "10. Copy of Aadhaar Card (Student and Parent)\n"
            "11. Anti-Ragging Undertakings signed online by student and parent on antiragging.in"
        ),
        "metadata": {"type": "checklist"}
    })
    chunk_counter += 1

    output_data = {
        "institution": "Narula Institute of Technology (NIT)",
        "source_url": "https://www.nit.ac.in/admission/",
        "total_chunks": len(chunks),
        "chunks": chunks
    }

    with open(UNSTRUCTURED_DATA_JSON, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)

    print(f"✓ Built knowledge base with {len(chunks)} chunks -> {UNSTRUCTURED_DATA_JSON}")
    return output_data

if __name__ == "__main__":
    build_knowledge_base()

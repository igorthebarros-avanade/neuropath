import PageTitle from "../global/PageTitle"

const container = `mb-4`

export default function Welcome(){
    return(
        <section className={container}>
            <PageTitle text="Welcome!"/>

            <p><b>Welcome to Avanade's Certification Buddy!</b> This tool uses artificial intelligence to provide smart practice questions, real-time feedback, and targeted content recommendations. This AI assistant will identify your strengths and weaknesses, and helps you focus on what matters most. With the Buddy, your study sessions become more efficient, focused, and effective, giving you the confidence and knowledge to succeed on exam day.</p>
        </section>
    )
}
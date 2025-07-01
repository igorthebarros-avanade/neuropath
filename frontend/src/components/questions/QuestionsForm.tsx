'use client'
import { FormEvent, useState } from "react"
import Select from "../global/Select"
import certifications from "@/src/domain/constants/certifications"
import Input from "../global/Input"
import Button from "../global/Button"
import apiService from '@/src/domain/services/apiService'
import Loading from "../global/Loading"
import { useRouter } from "next/navigation"


const inputs = `grid grid-cols-3 gap-4 mb-4`
const button = `flex items-center justify-center`

export default function QuestionsForm(){
    const router = useRouter()

    const [certification, setCertification] = useState(certifications[0])
    const [yesNoQuestions, setYesNoQuestions] = useState('')
    const [qualitativeQuestions, setQualitativeQuestions] = useState('')
    const [showLoading, setShowLoading] = useState(false)

    async function handleSubmit(e: FormEvent<HTMLFormElement>){
        e.preventDefault()
        setShowLoading(true)
        const generatedQuestions = (await apiService.getQuestions(certification, yesNoQuestions, qualitativeQuestions)).questions
        localStorage.setItem(
            `generatedQuestions-${certification}`, 
            JSON.stringify(generatedQuestions)
        )
        router.push(`/simulation?exam=${certification}`)
    }

    return (
        <form autoComplete="off" onSubmit={handleSubmit}>
            <div className={inputs}>
                <Select label="Select the certification" setValue={setCertification} value={certification} 
                options={certifications.map(c => {return {text: c, value: c}})}/>

                <Input isNumber label="Amount of yes/no questions" setValue={setYesNoQuestions} value={yesNoQuestions}/>
                
                <Input isNumber label="Amount of qualitative questions" setValue={setQualitativeQuestions} value={qualitativeQuestions}/>
            </div>
            
            <div className={button}>
                <Button isSubmit>Generate questions</Button>
            </div>

            {showLoading ?
                <Loading text={'Generating questions...'}/>
            : <></>}
        </form>
    )
}
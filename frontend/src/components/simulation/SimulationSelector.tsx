'use client'
import certifications from "@/src/domain/constants/certifications";
import Select from "../global/Select";
import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import Loading from "../global/Loading";
import Button from "../global/Button";
import { useSearchParams } from "next/navigation";
import { useRouter } from "next/navigation";

const inputs = `flex flex-col gap-4 items-center`
const link = `!underline`

export default function SimulationSelector(){
    const router = useRouter()
    const searchParams = useSearchParams()
    const defaultExam = searchParams.get('exam') || ''

    const [examsWithAvailableQuestions, setExamsWithAvailableQuestions] = useState<string[]>([''])
    const [selectedExam, setSelectedExam] = useState('')
    const [showLoading, setShowLoading] = useState(true)

    function handleSubmit(e: FormEvent<HTMLFormElement>){
        e.preventDefault()
        router.push(`/simulation/${selectedExam}`)
    }
    
    useEffect(() => {
        setExamsWithAvailableQuestions(
            certifications.filter(certification => localStorage.getItem(`generatedQuestions-${certification}`))
        )
    }, [])
    
    useEffect(() => {
        if(examsWithAvailableQuestions[0] != ''){
            setSelectedExam(
                examsWithAvailableQuestions.includes(defaultExam) ? defaultExam : examsWithAvailableQuestions[0]
            )
            setShowLoading(false)
        }
    }, [examsWithAvailableQuestions])

    return(
        <form autoComplete="off" onSubmit={handleSubmit}>
            {examsWithAvailableQuestions.length > 0 ?
                <div className={inputs}>
                    <Select label="Exams with available questions" options={examsWithAvailableQuestions.map(e => {
                        return {text: e, value: e}
                    })} setValue={setSelectedExam} value={selectedExam}/>

                    <Button isSubmit>Load questions</Button>
                </div>
            :
                <p>
                    There are no exams with available questions, go to the <Link className={link} href={'/questions'}>Questions Generator page</Link> and generate some for the desired certification.
                </p>
            }

            {showLoading ?
                <Loading text={'Fetching available questions...'}/>
            : <></>}
        </form>
    )
}